import tornado.ioloop
import tornado.web
import base64
import json
import os
import sys
import datetime

path = "../data_file/dangerous/"
dics = {}


class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        key = self.get_arguments('key')
        print(key)
        self.write("hi")

    def post(self):
        self.write("post")



def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print('server running: 0.0.0.0:8888')
    tornado.ioloop.IOLoop.current().start()
