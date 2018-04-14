#!/usr/bin/env python

import argparse
import datetime
import re
import collections
import os
import fnmatch
import gzip
import glob

DEFAULT_LOCAL_PATHS = 'var/log/:var/nvOS/etc/*/:var/nvOS/log/:var/lib/lxc/*/rootfs/:var/lib/lxc/*/rootfs/var/log'

CYEAR = datetime.datetime.now().year

# Number of lines to search on log file
# for datetime pattern before giving up
NUM_LINES_FOR_DT_PAT = 100

# https://docs.python.org/2/library/datetime.html

# \s+ => One or more white spaces
# Order is important here
DT_FORMATS = collections.OrderedDict()

#2018-02-08T17:06:33.088Z
DT_FORMATS['%Y-%m-%dT%H:%M:%S.%fZ'] = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}.\d{1,6}Z)')

# 2018-03-28,15:51:25.847
DT_FORMATS['%Y-%m-%d,%H:%M:%S.%f'] = re.compile(r'(\d{4}-\d{1,2}-\d{1,2},\d{1,2}:\d{1,2}:\d{1,2}.\d{1,6})')

# 2017-07-13 18:20:42
DT_FORMATS['%Y-%m-%d %H:%M:%S'] = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})')

# 2018-03-28,15:51:25
DT_FORMATS['%Y-%m-%d,%H:%M:%S'] = re.compile(r'(\d{4}-\d{1,2}-\d{1,2},\d{1,2}:\d{1,2}:\d{1,2})')

# Wed Apr  4 10:07:38 2018
DT_FORMATS['%a %b %d %H:%M:%S %Y'] = \
    re.compile(r'([A-Za-z]{3}\s*[A-Za-z]{3}\s*\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}\s+\d{4})')

# Apr  4 10:07:38 2018
DT_FORMATS['%b %d %H:%M:%S %Y'] = re.compile(r'([[A-Za-z]{3}\s*\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}\s+\d{4})')

# Apr04.10:08:08.800
DT_FORMATS['%b%d.%H:%M:%S.%f'] = re.compile(r'([A-Za-z]{3}\d{1,2}.\d{1,2}:\d{1,2}:\d{1,2}.\d{1,6})')

# Apr05.10:08:08
DT_FORMATS['%b%d.%H:%M:%S'] = re.compile(r'([A-Za-z]{3}\d{1,2}.\d{1,2}:\d{1,2}:\d{1,2})')

# 2013 Apr  8 17:15:02
DT_FORMATS['%Y %b %d %H:%M:%S'] = re.compile(r'(\d{4}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})')

# Apr  8 17:15:02 => syslog/kern.log/auth.log
DT_FORMATS['%b %d %H:%M:%S'] = re.compile(r'([A-Za-z]{3}\s+\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})')

# Sep09.15:41:57
DT_FORMATS['%b%d.%H:%M:%S'] = re.compile(r'([A-Za-z]{3}\s*\d{1,2}.\d{1,2}:\d{1,2}:\d{1,2})')


def test_df_formats():
    PRE = 'PRE'
    POST = 'POST'
    for dt in ('2018-02-08T17:06:33.088Z',
               '2018-03-28,15:51:25.847',
               '2017-07-13  18:20:42',
               '2018-03-28,15:51:25',
               'Apr04.10:08:08',
               'Apr04.10:08:08.800',
               '2013 Apr  8 17:15:02',
               'Apr  8 17:15:02',
               'Sep09.15:41:57',
               'Wed Apr  4 10:07:38 2018',
               'Apr  4 10:07:38 2018'):
        assert mydt(PRE + dt + POST).ext_dt == dt


class mydt:
    """
    Helper class to maintain datetime to compare logs
    """
    def __init__(self, line, i_df=None):
        # Given line with datetimestamp
        self.line = line
        # Extracted dt string
        self.ext_dt = None
        self.dt_pat = None
        # dt is python datetime object
        self.dt = None
        self.sec = None
        self.usec = None

        if i_df is not None:
            # if the pattern is specified,
            # no need to search all the possibilities
            all_dt = [(i_df, DT_FORMATS[i_df])]
        else:
            all_dt = DT_FORMATS.iteritems()

        for df, rpat in all_dt:
            try:
                self.ext_dt = self._extract_dt_from_line(rpat)
                if self.ext_dt is None:
                    continue
                self.dt = self._get_python_dt(df)
                self.dt_pat = df
                break
            except ValueError:
                pass
        if self.dt is None:
            raise ValueError

        self.sec = int(self.dt.strftime('%s'))
        self.usec = int(self.sec * 10 ** 6) + int(self.dt.strftime('%f'))

    def _extract_dt_from_line(self, rpat):
        if rpat is not None:
            rsrc = rpat.search(self.line)
            if rsrc is None:
                return None
            return rsrc.group()
        else:
            return self.line

    def _get_python_dt(self, df):
        if ('y' not in df) and ('Y' not in df):
            # dt does not have year in it, add current year
            # This will be useful to compare dts
            return datetime.datetime.strptime(str(CYEAR) + self.ext_dt, '%Y' + df)
        else:
            return datetime.datetime.strptime(self.ext_dt, df)

    @staticmethod
    def getdt(line, pat):
        try:
            _dt = mydt(line, pat)
            return _dt
        except ValueError:
            return None

    @staticmethod
    def get_sec_usec(val):
        sec = 0
        usec = 0
        if 'us' in val:
            usec = int(val.replace('us', ''))
        elif 'ms' in val:
            val = int(val.replace('ms', ''))
            usec = 1000 * val
        elif 's' in val:
            val = int(val.replace('s', ''))
            usec = 1000 * 1000 * val
            sec = val
        elif 'm' in val:
            val = int(val.replace('m', ''))
            usec = 1000 * 1000 * 60 * val
            sec = 60 * val
        else:
            val = int(val)
            usec = 1000 * 1000 * val
            sec = val
        return sec, usec

    def add(self, val):
        sec, usec = self.get_sec_usec(val)
        self.sec += sec
        self.usec += usec

    def sub(self, val):
        sec, usec = self.get_sec_usec(val)
        self.sec -= sec
        self.usec -= usec

    def __str__(self):
        return '%s => dt=%s, sec=%d, usec=%d' % (self.ext_dt, str(self.dt), self.sec, self.usec)

    def __call__(self, *args, **kwargs):
        return self.usec


def get_dt1_dt2(dt_str):
    try:
        if '@' not in dt_str:
            l_trange = None
            h_trange = None
            if '+-' in dt_str:
                dt_str, trange = dt_str.split('+-')
                l_trange = trange
                h_trange = trange
            elif '+' in dt_str and '-' in dt_str:
                plus_i = dt_str.index('+')
                minus_i = dt_str.index('-')

                if plus_i < minus_i:
                    dt_str, trange = dt_str.split('+')
                    h_trange, l_trange = trange.split('-')
                else:
                    dt_str, trange = dt_str.split('-')
                    l_trange, h_trange = trange.split('+')
            elif '-' in dt_str:
                dt_str, trange = dt_str.split('-')
                l_trange = trange
            elif '+' in dt_str:
                dt_str, trange = dt_str.split('+')
                h_trange = trange
            else:
                dt_str = dt_str

            _dt1 = mydt(dt_str)
            _dt2 = mydt(dt_str)

            if l_trange is not None and h_trange is not None:
                _dt1.sub(l_trange)
                _dt2.add(h_trange)
            elif l_trange is not None:
                _dt1.sub(l_trange)
            elif h_trange is not None:
                _dt2.add(h_trange)
            return _dt1, _dt2

        else:
            dt1_str, dt2_str = dt_str.split('@')
            _dt1 = mydt(dt1_str)
            _dt2 = mydt(dt2_str)

            if _dt1() < _dt2():
                return _dt1, _dt2
            else:
                return _dt2, _dt1

    except ValueError:
        msg = "Given Date ({0}) not valid! Expected format, {1}".format(dt_str, str(DT_FORMATS.keys()))
        raise argparse.ArgumentTypeError(msg)


def get_all_files(search_dir, paths, pats):
    files = []
    if paths == '*':
        for dirpath, dirnames, filenames in os.walk(search_dir, followlinks=False):
            for pat in pats.split(','):
                for f in fnmatch.filter(filenames, pat):
                    files.append(os.path.join(dirpath, f))
    else:
        for path in paths.split(':'):
            for pat in pats.split(','):
                for f in glob.glob(os.path.join(search_dir, path, pat)):
                    if os.path.isfile(f):
                        files.append(f)
    return files


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class logFile:
    def __init__(self, file, dt1, dt2, options):
        self.filename = file
        self.is_gz = self.filename.endswith('gz')
        self.lines = []
        self._get_dt_pat(dt1, dt2, options)

    def _fopen(self):
        if self.is_gz:
            fopen = gzip.open
        else:
            fopen = open
        return fopen

    def _get_dt_pat(self, dt1, dt2, options):
        """
        Reads few lines from the file and 
        return the datetime pattern that the file belongs to
        """
        dt_pat = None
        first_dt = None
        last_dt = None

        with self._fopen()(self.filename) as fp:
            all_lines = fp.readlines()

        for n_line, line in enumerate(all_lines, 1):
            try:
                first_dt = mydt(line)
                dt_pat = first_dt.dt_pat
                break
            except ValueError:
                pass
            if n_line > NUM_LINES_FOR_DT_PAT:
                break

        if dt_pat is None:
            return

        for n_line, line in enumerate(reversed(all_lines), 1):
            try:
                last_dt = mydt(line)
                break
            except ValueError:
                pass
            if n_line > NUM_LINES_FOR_DT_PAT:
                break

        if self.is_log_ordered(first_dt, last_dt):
            if first_dt.usec > dt2.usec or last_dt.usec < dt1.usec:
                return

        written_something = False
        for ln, line in enumerate(all_lines, 1):
            try:
                line_dt = mydt(line, dt_pat)
                if self.is_log_ordered(first_dt, last_dt) and line_dt.usec > dt2.usec:
                    break
                elif dt1.usec <= line_dt.usec <= dt2.usec:
                    self.lines.append(self.get_formatted_line(ln, line, options))
                    written_something = True
            except ValueError:
                if written_something:
                    # Lines without dt is appended as part of prev lines
                    self.lines.append(self.get_formatted_line(ln, line, options))

    @staticmethod
    def is_log_ordered(first_dt, last_dt):
        if first_dt is not None and last_dt is not None and \
                        first_dt.usec <= last_dt.usec:
            return True
        else:
            return False

    def get_formatted_line(self, ln, line, options):
        if options.ignore_lineno:
            line_to_add = line
        elif options.ignore_color:
            line_to_add = str(ln) + ':' + ' ' + line
        else:
            line_to_add = bcolors.WARNING + str(ln) + ':' + bcolors.ENDC + ' ' + line
        return line_to_add

    def print_lines(self):
        if len(self.lines):
            print('\n========================= %s =========================\n' % self.filename)
            print ''.join(self.lines)
            print '\n'


def get_options():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--dt', required=True, help='Starting datetime')
    parser.add_argument('--dir', default=os.getcwd(), help='Directory to search log files (default cwd: %(default)s)')
    parser.add_argument('--path', default=DEFAULT_LOCAL_PATHS,
                        help='Path to search (: separated) undir --dir, if * is given recursively searched (default: \'%(default)s\')')
    parser.add_argument('--pat', default='*log*',
                        help='Pattern(unix shell style) to search (, separated) log files, provide within quote: (default: \'%(default)s\')')

    parser.add_argument('-l', '--local', action='store_true', help='Local log search --dir will be set to \'\\\'')

    parser.add_argument('--ignore_color', action='store_true', help='Ignore color in line number')
    parser.add_argument('--ignore_lineno', action='store_true', help='Ignore line number')

    return parser.parse_args()


def main():
    options = get_options()
    dt1, dt2 = get_dt1_dt2(options.dt)

    if options.local:
        options.dir = '/'

    for f in get_all_files(options.dir, options.path, options.pat):
        lf = logFile(f, dt1, dt2, options)
        lf.print_lines()

if __name__ == '__main__':
    main()
