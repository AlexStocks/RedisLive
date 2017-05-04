#!/bin/python
# -*- coding: UTF-8 -*-
# ******************************************************
# DESC    : run redis-monitor.py every minute
# AUTHOR  : Alex Stocks
# VERSION : 1.0
# LICENCE : LGPL V3
# EMAIL   : alexstocks@foxmail.com
# MOD     : 2016-04-10 06:07
# FILE    : crontab.py
# ******************************************************

import os, sched, time
import logging
from api.util import log

tv = 5
s = sched.scheduler(time.time, time.sleep)
def run(sc, cmd):
    # print "Doing stuff..."
    #cmd = 'echo hello'
    logging.info("info log test")
    logging.debug("debug log test")
    os.system(cmd)
    sc.enter(tv, 1, run, (sc, cmd))

if __name__ == "__main__":
    cwd = os.path.dirname(os.path.realpath(__file__))
    # log.init_log(cwd + '/monitor-log/crontab.log', logging.INFO)
    log.init_log(cwd + '/monitor-log/crontab.log', logging.DEBUG)
    logging.info('crontab starting...')

    cmd = 'echo "hello"'
    s.enter(tv, 1, run, (s, cmd))
    s.run()
