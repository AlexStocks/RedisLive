#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ******************************************************
# DESC    :
# AUTHOR  : Alex Stocks
# VERSION : 1.0
# LICENCE : LGPL V3
# EMAIL   : alexstocks@foxmail.com
# MOD     : 2016-04-14 17:06
# FILE    : crontab-monitor.py
# ******************************************************

import os, sched, time
import logging
from api.util import log

tv = 60
sched1 = sched.scheduler(time.time, time.sleep)
def run(sc, cmds):
    # print "Doing stuff..."
    #cmd = 'echo hello'
    logging.info("info log test")
    logging.debug("debug log test")
    for cmd in cmds:
        print cmd
        os.system(cmd)
    sc.enter(tv, 1, run, (sc, cmds))

if __name__ == "__main__":
    cwd = os.path.dirname(os.path.realpath(__file__))
    # log.init_log(cwd + '/monitor-log/crontab.log', logging.INFO)
    log.init_log(cwd + '/monitor-log/crontab.log', logging.DEBUG)
    logging.info('crontab starting...')

    cmds = []
    # cmds.append('echo "hello"')
    # cmds.append('echo "world"')
    cmds.append('cd ../../client && sh benchmark.sh 6414 && cd -')
    cmds.append('cd ../../client && sh benchmark.sh 6415 && cd -')
    sched1.enter(tv, 1, run, (sched1, cmds))
    sched1.run()

