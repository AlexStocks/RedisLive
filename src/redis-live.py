
#! /usr/bin/env python

import os

import tornado.ioloop
import tornado.options
from tornado.options import define, options
import tornado.web

from api.controller.BaseStaticFileHandler import BaseStaticFileHandler

from api.controller.ServerListController import ServerListController
from api.controller.InfoController import InfoController
from api.controller.MemoryController import MemoryController
from api.controller.CommandsController import CommandsController
from api.controller.HitRateController import HitRateController
from api.controller.KeySpaceController import KeySpaceController
from api.controller.ExpiredEvictedController import ExpiredEvictedController
from api.controller.TopCommandsController import TopCommandsController
from api.controller.TopKeysController import TopKeysController

import logging
from api.util import log

if __name__ == "__main__":
    cwd = os.path.dirname(os.path.realpath(__file__))
    log.init_log(cwd + '/monitor-log/redis-live.log', logging.DEBUG)
    logging.info('redis-live starting...')

    define("port", default=8888, help="run on the given port", type=int)
    define("debug", default=0, help="debug mode", type=int)
    tornado.options.parse_command_line()

    # Bootup
    handlers = [
    (r"/api/servers", ServerListController),
    (r"/api/info", InfoController),
    (r"/api/memory", MemoryController),
    (r"/api/commands", CommandsController),
    (r"/api/hitrate", HitRateController),
    (r"/api/keyspace", KeySpaceController),
    (r"/api/expired-evicted", ExpiredEvictedController),
    (r"/api/topcommands", TopCommandsController),
    (r"/api/topkeys", TopKeysController),
    (r"/(.*)", BaseStaticFileHandler, {"path": "www"})
    ]

    server_settings = {'debug': options.debug}
    application = tornado.web.Application(handlers, **server_settings)
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
