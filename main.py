#!/usr/bin/env python2.6
# encoding: utf-8
"""
main.py

"""
import os

# Importing tornado's stuff
import asyncmongo
import brukva
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options

# Import controllers
import controllers.main
import controllers.board
import controllers.thread

# Import models
import models.board
import models.thread

# Options defines
define("host", default='127.0.0.1', help="run on the given address", type=str)
define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="debug mode", type=bool)
# Redis
define("redis_host", default='localhost', help="redis host", type=str)
define("redis_port", default=6379, help="redis port", type=int)
define("redis_password", default='', help="redis password", type=str)
# Mongo
define("mongo_host", default='127.0.0.1', help="mongo host", type=str)
define("mongo_port", default=27107, help="mongo port", type=int)
define("mongo_maxcached", default=10, help="mongo maxcached", type=int)
define("mongo_maxconn", default=50, help="mongo max connections", type=int)
define("mongo_db", default='test', help="mongo database name", type=str)


class Klipped(tornado.web.Application):
    """ Main application class """
    def __init__(self):
        # Redis
        self.redis = brukva.Client(host=options.redis_host, port=options.redis_port)
        self.redis.connect()
        if options.redis_password:
            self.redis.auth(options.redis_password)
        # Models
        self.board = models.board.BoardModel(self)
        self.thread = models.thread.ThreadModel(self)
        # Mongo
        #self.mongo = asyncmongo.Client(host=options.mongo_host, 
        #                               port=options.mongo_port,
        #                               maxcached=options.mongo_maxcached, 
        #                               maxconnections=options.mongo_maxconn, 
        #                               dbname=options.mongo_db)
        # Routes
        # TODO: Fix regexps
        handlers = [
            (r"/", controllers.main.MainHandler),
            (r"/([a-z]+).([a-z]+)", controllers.board.BoardHandler),
            (r"/([a-z]+)/([0-9]+).([a-z]+)", controllers.thread.ThreadHandler),
        ]
        # Settings
        settings = {'debug': options.debug,
                    'template_path': os.path.join(os.path.dirname(__file__), "views")
        }
        super(Klipped, self).__init__(handlers=handlers, **settings)

    def listen(self, port, address="", **kwargs):
        """Starts an HTTP server for this application on the given port."""
        # Backported from tornado git
        from tornado.httpserver import HTTPServer
        server = HTTPServer(self, **kwargs)
        server.listen(port, address)

def main():
    tornado.options.parse_config_file("klipped.conf")
    tornado.options.parse_command_line()
    application = Klipped()
    application.listen(options.port, address=options.host)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	main()

