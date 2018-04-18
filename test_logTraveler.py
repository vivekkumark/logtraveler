#!/usr/bin/env python

from logTraveler import mydt


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
