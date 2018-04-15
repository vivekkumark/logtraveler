# logtraveler
A simple tool to filter lines of log files of given datetime range.

Often times while debugging issues,
we will be interested in quickly walk through log lines of
specific datetimestamp or a datetimespan of tenths of different 
log files in various directories.
This is especially needed for coordinated micro services running on a host 
or services that are running across hosts in a distributed systems.
It will be more cumbersome, if different datetime format is 
used in across log files.  

## Features


## Usage

```
usage: logTraveler.py [-h] -d DT [--dir DIR] [-l] [-s SUB] [-f FILE]
                      [--ignore_lineno] [-c] [-n NUM_LINES]

optional arguments:
  -h, --help            show this help message and exit
  -d DT, --dt DT        datetime to filter lines('dt1@dt2' or 'dt' or
                        'dt+num[us|ms|s|m]' or 'dt-num[us|ms|s|m]' or
                        'dt+-num[us|ms|s|m]')
  --dir DIR             comma separated list of directory to search (default
                        cwd: '/Users/vkuma/IdeaProjects/logtraveler')
  -l, --local           Local log search, --dir will be set to '\'
  -s SUB, --sub SUB     comma separated subdirs pattern to search within --dir
                        , if just '*' is passed recursively searched on all
                        subdirs(default: 'var/log/ , var/nvOS/etc/*/ ,
                        var/nvOS/log/ , var/lib/lxc/*/rootfs/ ,
                        var/lib/lxc/*/rootfs/var/log')
  -f FILE, --file FILE  comma separated file name patterns, provide within
                        quote: (default: '*log*')
  --ignore_lineno       Ignore line number
  -c, --ignore_color    Ignore color
  -n NUM_LINES, --num_lines NUM_LINES
                        Number of lines to search to classify datetime in a
                        file(default: 100)
```
## How to install?

Make sure the machine has python installed in it (version >= 2.7)

**curl https://raw.githubusercontent.com/vivekkns/logtraveler/master/logTraveler.py > logTraveler.py; chmod +x logTraveler.py**

... and to make it handy, add the dir in PATH variable in your
.bashrc or .bash_profile or
any script that is used for initializing your shell session
