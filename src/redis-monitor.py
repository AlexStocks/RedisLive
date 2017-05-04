#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# ******************************************************
# DESC    :
# AUTHOR  : Alex Stocks
# VERSION : 1.0
# LICENCE : LGPL V3
# EMAIL   : zhaoxin@zenmen.com
# MOD     : 2016-04-14 16:57
# FILE    : redis-monitor.py
# ******************************************************

from api.util import settings
from dataprovider.dataprovider import RedisLiveDataProvider
from threading import Timer
import redis
import datetime
import threading
import traceback
import argparse
import time

import os
import logging
from api.util import log

def isClose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def isZero(a):
    return isClose((float)(a), 0.0)

class Monitor(object):
    """Monitors a given Redis server using the MONITOR command.
    """

    def __init__(self, connection_pool):
        """Initializes the Monitor class.

        Args:
            connection_pool (redis.ConnectionPool): Connection pool for the \
                    Redis server to monitor.
        """
        self.connection_pool = connection_pool
        self.connection = None

    def __del__(self):
        try:
            self.reset()
        except:
            pass

    def reset(self):
        """If we have a connection, release it back to the connection pool.
        """
        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def monitor(self):
        """Kicks off the monitoring process and returns a generator to read the
        response stream.
        """
        if self.connection is None:
            self.connection = self.connection_pool.get_connection('monitor', None)
        self.connection.send_command("monitor")
        return self.listen()

    def parse_response(self):
        """Parses the most recent responses from the current connection.
        """
        return self.connection.read_response()

    def listen(self):
        """A generator which yields responses from the MONITOR command.
        """
        while True:
            yield self.parse_response()

class MonitorThread(threading.Thread):
    """Runs a thread to execute the MONITOR command against a given Redis server
    and store the resulting aggregated statistics in the configured stats
    provider.
    """

    def __init__(self, server, port, password=None):
        """Initializes a MontitorThread.

        Args:
            server (str): The host name or IP of the Redis server to monitor.
            port (int): The port to contact the Redis server on.

        Kwargs:
            password (str): The password to access the Redis host. Default: None
        """
        super(MonitorThread, self).__init__()
        self.server = server
        self.port = port
        self.password = password
        self.id = self.server + ":" + str(self.port)
        self._stop = threading.Event()

    def stop(self):
        """Stops the thread.
        """
        self._stop.set()

    def stopped(self):
        """Returns True if the thread is stopped, False otherwise.
        """
        return self._stop.is_set()

    def run(self):
        """Runs the thread.
        """
        stats_provider = RedisLiveDataProvider.get_provider()
        pool = redis.ConnectionPool(host=self.server, port=self.port, db=0,
                                    password=self.password)
        monitor = Monitor(pool)
        commands = monitor.monitor()
        # 460536854.885963 [0 10.136.40.61:47942] "ZUNIONSTORE" "_top_counts" "86407" "10.136.40.61:6415:CommandCount:1459932070" "10.136.40.61:6415:CommandCount:1459932071"
        # "10.136.40.61:6415:CommandCount:1459932072"

        for command in commands:
            # logging.debug("id:%s, command:%s" % (self.id, command))
            try:
                parts = command.split(" ")

                if len(parts) == 1:
                    continue

                epoch = float(parts[0].strip())
                timestamp = datetime.datetime.fromtimestamp(epoch)

                # Strip '(db N)' and '[N x.x.x.x:xx]' out of the monitor str
                if (parts[1] == "(db") or (parts[1][0] == "["):
                    parts = [parts[0]] + parts[3:]

                command = parts[1].replace('"', '').upper()

                if len(parts) > 2:
                    keyname = parts[2].replace('"', '').strip()
                else:
                    keyname = None

                if len(parts) > 3:
                    # TODO: This is probably more efficient as a list
                    # comprehension wrapped in " ".join()
                    arguments = ""
                    for x in xrange(3, len(parts)):
                        arguments += " " + parts[x].replace('"', '')
                    arguments = arguments.strip()
                else:
                    arguments = None
                logging.debug("id:%s, epoch%s, timestamp:%s, command:%s, keyname:%s, arguments:%s"
                                % (self.id, epoch, timestamp, command, keyname, arguments))

                # 不把RedisLive发出的info 和 monitor命令统计在内
                if not command == 'INFO' and not command == 'MONITOR':
                    stats_provider.save_monitor_command(self.id,        # server id，如 10.136.40.61:6414
                                                        timestamp,      # 命令操作时的时间，如 2016-04-13 16:26:    13.266209
                                                        command,        # redis命令
                                                        str(keyname),   # key
                                                        str(arguments)) # value

                # 从line 142到line146调用stats_provider.save_monitor_command的log内容如下：
                """
                DEBUG: 04-14 15:12:20: redis-monitor.py:142 * 6560 id:10.136.40.61:6414, epoch1460617919.08, timestamp:2016-04-14 15:11:59.083228, command:PING, keyname:None, arguments:None
                DEBUG: 04-14 15:12:20: redisprovider.py:61 * 6560 epoch:1460646719, current_date:160414
                DEBUG: 04-14 15:12:20: redisprovider.py:73 * 6560 command_count_key:10.136.40.61:6414:CommandCount:1460646719, command:PING
                DEBUG: 04-14 15:12:20: redisprovider.py:77 * 6560 command_count_key:10.136.40.61:6414:DailyCommandCount:160414, command:PING
                DEBUG: 04-14 15:12:20: redisprovider.py:81 * 6560 key_count_key:10.136.40.61:6414:KeyCount:1460646719, keyname:None
                DEBUG: 04-14 15:12:20: redisprovider.py:85 * 6560 key_count_key:10.136.40.61:6414:DailyKeyCount:160414, keyname:None
                DEBUG: 04-14 15:12:20: redisprovider.py:90 * 6560 command_count_key:10.136.40.61:6414:CommandCountBySecond, epoch:1460646719
                DEBUG: 04-14 15:12:20: redisprovider.py:96 * 6560 command_count_key:10.136.40.61:6414:CommandCountByMinute, field name:160414:15:11
                DEBUG: 04-14 15:12:20: redisprovider.py:101 * 6560 command_count_key:10.136.40.61:6414:CommandCountByHour, field name:160414:15
                DEBUG: 04-14 15:12:20: redisprovider.py:106 * 6560 command_count_key:10.136.40.61:6414:CommandCountByDay, field name:160414
                """

            except Exception, e:
                tb = traceback.format_exc()
                print "==============================\n"
                print datetime.datetime.now()
                print tb
                print command
                print "==============================\n"

            if self.stopped():
                break

class InfoThread(threading.Thread):
    """Runs a thread to execute the INFO command against a given Redis server
    and store the resulting statistics in the configured stats provider.
    """

    def __init__(self, server, port, password=None):
        """Initializes an InfoThread instance.

        Args:
            server (str): The host name of IP of the Redis server to monitor.
            port (int): The port number of the Redis server to monitor.

        Kwargs:
            password (str): The password to access the Redis server. \
                    Default: None
        """
        threading.Thread.__init__(self)
        self.server = server
        self.port = port
        self.password = password
        self.id = self.server + ":" + str(self.port)
        logging.info('InfoThread server_id:%s' % (self.id))
        self._stop = threading.Event()

    def stop(self):
        """Stops the thread.
        """
        self._stop.set()

    def stopped(self):
        """Returns True if the thread is stopped, False otherwise.
        """
        return self._stop.is_set()

    def run(self):
        """Does all the work.
        """
        stats_provider = RedisLiveDataProvider.get_provider()
        redis_client = redis.StrictRedis(host=self.server, port=self.port, db=0,
                                        password=self.password)

        # process the results from redis
        while not self.stopped():
            try:
                redis_info = redis_client.info()
                current_time = datetime.datetime.now()
                used_memory = int(redis_info['used_memory'])
                keyspace_hits = float(redis_info['keyspace_hits'])
                keyspace_misses = float(redis_info['keyspace_misses'])
                keyspace_sum = keyspace_hits + keyspace_misses
                keyspace_hit_rate = 0

                keyspace_keys = int(redis_info['db0']['keys'])
                keyspace_expires = int(redis_info['db0']['expires'])

                stat_expired_keys = int(redis_info['expired_keys'])
                stat_evicted_keys = int(redis_info['evicted_keys'])

                if not isZero(keyspace_sum):
                    keyspace_hit_rate = int(100 * (keyspace_hits / keyspace_sum))

                # used_memory_peak not available in older versions of redis
                try:
                    peak_memory = int(redis_info['used_memory_peak'])
                except:
                    peak_memory = used_memory
                logging.debug('id:%s, redis_info:%s' % (self.id, redis_info))
                logging.debug('id:%s, used_memory:%s, used_memory_peak:%s, keys:%s, expires:%s'
                                % (self.id, used_memory, peak_memory, keyspace_keys, keyspace_expires))
                # id:10.136.40.61:6415, redis_info:xx, used_memory:264050976, used_memory_peak:271452984
                # id:10.136.40.61:6415, redis_info:xx, used_memory:264050976, used_memory_peak:271452984

                stats_provider.save_memory_info(self.id, current_time,
                                                used_memory, peak_memory)

                stats_provider.save_keyspace_info(self.id, current_time,
                                                keyspace_keys, keyspace_expires)

                stats_provider.save_expired_evicted_info(self.id, current_time,
                                                stat_expired_keys, stat_evicted_keys)

                stats_provider.save_hitrate_info(self.id, current_time, keyspace_hit_rate)
                stats_provider.save_info_command(self.id, current_time,
                                                 redis_info)

                # databases=[]
                # for key in sorted(redis_info.keys()):
                #     if key.startswith("db"):
                #         database = redis_info[key]
                #         database['name']=key
                #         databases.append(database)

                # expires=0
                # persists=0
                # for database in databases:
                #     expires+=database.get("expires")
                #     persists+=database.get("keys")-database.get("expires")

                # stats_provider.SaveKeysInfo(self.id, current_time, expires, persists)

                time.sleep(1)

            except Exception, e:
                tb = traceback.format_exc()
                print "==============================\n"
                print datetime.datetime.now()
                print tb
                print "==============================\n"

class RedisMonitor(object):

    def __init__(self):
        logging.debug("RedisMonitor __init__()")
        self.threads = []
        self.active = True

    def run(self, duration):
        """Monitors all redis servers defined in the config for a certain number
        of seconds.

        Args:
            duration (int): The number of seconds to monitor for.
        """
        logging.debug("RedisMonitor run()")
        redis_servers = settings.get_redis_servers()

        logging.debug("redis_servers:%s" % redis_servers)
        for redis_server in redis_servers:
            logging.debug("redis_server:%s" % redis_server)

            redis_password = redis_server.get("password")

            monitor = MonitorThread(redis_server["server"], redis_server["port"], redis_password)
            self.threads.append(monitor)
            monitor.setDaemon(True)
            monitor.start()

            info = InfoThread(redis_server["server"], redis_server["port"], redis_password)
            self.threads.append(info)
            info.setDaemon(True)
            info.start()

        t = Timer(duration, self.stop)
        t.start()

        try:
            while self.active:
                pass
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            t.cancel()

    def stop(self):
        """Stops the monitor and all associated threads.
        """
        logging.debug("RedisMonitor stop()")
        if args.quiet==False:
            print "shutting down..."
        for t in self.threads:
                t.stop()
        self.active = False


if __name__ == '__main__':
    cwd = os.path.dirname(os.path.realpath(__file__))
    log.init_log(cwd + '/monitor-log/redis-monitor.log', logging.DEBUG)
    logging.info('redis-monitor starting...')

    parser = argparse.ArgumentParser(description='Monitor redis.')
    parser.add_argument('--duration',
                        type=int,
                        help="duration to run the monitor command (in seconds)",
                        required=True)
    parser.add_argument('--quiet',
                        help="do  not write anything to standard output",
                        required=False,
                        action='store_true')
    args = parser.parse_args()
    duration = args.duration
    monitor = RedisMonitor()
    monitor.run(duration)
