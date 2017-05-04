#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ******************************************************
# DESC    :
# AUTHOR  : Alex Stocks
# VERSION : 1.0
# LICENCE : LGPL V3
# EMAIL   : alexstocks@foxmail.com
# MOD     : 2016-04-14 17:04
# FILE    : HitRateController.py
# ******************************************************

from __future__ import print_function
from BaseController import BaseController
import tornado.ioloop
import tornado.web
import dateutil.parser
from datetime import datetime, timedelta
import logging
from api.util import log

class HitRateController(BaseController):

    def get(self):
        """Serves a GET request

        """
        logging.debug("HitRateController::get()")
        return_data = dict(data=[], timestamp=datetime.now().isoformat())

        server = self.get_argument("server")
        from_date = self.get_argument("from", None)
        to_date = self.get_argument("to", None)

        if not from_date or not to_date:
            end = datetime.now()
            delta = timedelta(seconds=120)
            start = end - delta
        else:
            start = dateutil.parser.parse(from_date)
            end = dateutil.parser.parse(to_date)

        difference = end - start
        # added to support python version < 2.7, otherwise timedelta has
        # total_seconds()
        difference_total_seconds = difference.days * 24 * 3600
        difference_total_seconds += difference.seconds
        difference_total_seconds += difference.microseconds / 1e6

        minutes = difference_total_seconds / 60
        hours = minutes / 60
        seconds = difference_total_seconds

        if hours > 120:
          group_by = "day"
        elif minutes > 120:
          group_by = "hour"
        elif seconds > 120:
          group_by = "minute"
        else:
          group_by = "second"

        # logging.debug("server:%s, from_date:%s, to_date:%s, start:%s, end:%s, difference:%s, difference_total_seconds:%s, hours:%s, minutes:%s, seconds:%s, group_by:%s"
#                % (server, from_date, to_date, start, end, difference, difference_total_seconds, hours, minutes, seconds, group_by))

        # print("server:%s, from_date:%s, to_date:%s, start:%s, end:%s, difference:%s, difference_total_seconds:%s, hours:%s, minutes:%s, seconds:%s, group_by:%s"
#                % (server, from_date, to_date, start, end, difference, difference_total_seconds, hours, minutes, seconds, group_by))

        combined_data = []
        stats = self.stats_provider.get_hit_rate_stats(server, start, end,
                                                      group_by)
        # print("get_command_stats(server:%s, start:%s, end:%s, group_by:%s) = " % (server, start, end, group_by))
        # print("get_command_stats(server:%s, start:%s, end:%s, group_by:%s) = " % (server, start, end, group_by), *stats)
        # print("\n")
        # print(*stats, sep='\t')
        for data in stats:
            combined_data.append([data[1], data[0]])
            # print("stat data:%r" % data)
        # print(*combined_data, sep='\t')
        for data in combined_data:
            return_data['data'].append([self.datetime_to_list(data[0]), data[1]])
            # print("combined_data:%r, return_data['data']:%s %r" % (data, return_data['data'], return_data['data']))
        # print('return_data:%s' % return_data)
        self.write(return_data)
