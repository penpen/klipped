#!/usr/bin/env python
# encoding: utf-8
"""
thread.py

Thread controller
"""

import tornado.web
from brukva import adisp
from functools import partial
import simplejson
import time, datetime
async = partial(adisp.async, cbname='callbacks')

def timestamp(datetime_obj):
    """ Convert datetime object to timestamp """
    if type(datetime_obj) is datetime.datetime:
        return int(time.mktime(datetime_obj.timetuple()))
    else:
        return int(datetime_obj)

class ThreadHandler(tornado.web.RequestHandler):
    """ Thread handler """
    @tornado.web.asynchronous
    @adisp.process
    def get(self, board, thread, format='html'):
        """ Returns thread (list of posts) """
        (_, post_count) = yield async(self.application.redis.get)("thread:{board}:{thread}:posts_counts".format(board=board, thread=thread))
        (_, posts_ids) = yield async(self.application.redis.lrange)("thread:{board}:{thread}:posts".format(board=board, thread=thread), 0, 10)
        ids_keys = ["post:{board}:{thread}:{post_id}:json".format(board=board, thread=thread, post_id=post_id) for post_id in posts_ids]
        (_, posts) = yield async(self.application.redis.mget)(ids_keys)
        self.render("thread.html", title="My title", posts=posts, post_count=post_count)

    @tornado.web.asynchronous
    @adisp.process
    def post(self, board, thread, format='html'):
        """ Adding new post to thread """
        data = {}
        for field in ['subject', 'author', 'email', 'password', 'body']:
            if self.get_argument(field, None):
                data[field] = self.get_argument(field, None)
        self.set_header("Content-Type", "text/plain")

        (_, key) = yield async(self.application.redis.incr)("board:{board}:id".format(board=board))
        print key
        data['id'] = key
        data['date'] = timestamp(datetime.datetime.now())
        # Update thread post counts
        self.application.redis.incr("thread:{board}:{thread}:posts_counts".format(board=board, thread=thread))
        # Adding post to db
        self.application.redis.set("post:{board}:{thread}:{post_id}:json".format(board=board, thread=thread, post_id=key), simplejson.dumps(data))
        # Adding post to thread
        self.application.redis.rpush("thread:{board}:{thread}:posts".format(board=board, thread=thread), key)
        # Up thread
        self.application.redis.zrem("board:{board}:threads".format(board=board), thread)
        self.application.redis.zadd("board:{board}:threads".format(board=board), timestamp(datetime.datetime.now()), thread)
        self.redirect('/{board}/{thread}.html'.format(board=board, thread=thread))
