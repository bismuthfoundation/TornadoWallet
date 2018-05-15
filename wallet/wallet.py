"""
Proof of concept Python/HTML Wallet for Bismuth, Tornado based
"""

import os.path
import re
import random
import string
import time
import datetime
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
import unicodedata

from tornado.options import define, options

__version__ = '0.0.1'

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/transactions", TransactionsHandler),
        ]
        settings = dict(
            app_title=u"Tornado Bismuth Wallet",
            template_path=os.path.join(os.path.dirname(__file__), "theme"),
            static_path=os.path.join(os.path.dirname(__file__), "theme/static"),
            ui_modules={"Transaction": TxModule},
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    pass


class HomeHandler(BaseHandler):
    async def get(self):
        """
        :return:
        """
        self.render("home.html", balance="101")


class TransactionsHandler(BaseHandler):

    def randhex(self, size):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=size))

    def tx(self, i):
        """
        fake tx
        :return:
        """
        txdate = time.time() - i * 5
        txdate = datetime.datetime.fromtimestamp(int(txdate)).strftime('%Y-%m-%d %H:%M:%S')
        return {'txid': self.randhex(32), 'address': self.randhex(32), 'recipient': self.randhex(32),
                'amount': str(random.randint(1,100)/10), 'date': txdate,
                'openfield': self.randhex(10), 'fees': '0.01'}

    async def get(self):
        """
        :return:
        """
        self.render("transactions.html", transactions=[self.tx(i) for i in range(15)])


class TxModule(tornado.web.UIModule):
    def render(self, tx):
        return self.render_string("modules/transaction.html", tx=tx)


async def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    # In this demo the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
