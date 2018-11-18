"""
Proof of concept Python/HTML Wallet for Bismuth, Tornado based

Use --help command line switch to get usage.
"""

import os.path
import re
import json
import logging
import random
import string
import time
import datetime
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.locks
import tornado.options
import tornado.web
import unicodedata

from tornado.options import define, options
# from bismuthclient import bismuthapi
from bismuthclient import bismuthclient

__version__ = '0.0.2'

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="debug mode", type=bool)
define("verbose", default=False, help="verbose mode", type=bool)


class Application(tornado.web.Application):
    def __init__(self):
        # wallet_servers = bismuthapi.get_wallet_servers_legacy()
        bismuth_client = bismuthclient.BismuthClient(verbose=options.verbose)
        handlers = [
            (r"/", HomeHandler),
            (r"/transactions", TransactionsHandler),
            (r"/json/(.*)", JsonHandler)
        ]
        settings = dict(
            app_title=u"Tornado Bismuth Wallet",
            template_path=os.path.join(os.path.dirname(__file__), "theme"),
            static_path=os.path.join(os.path.dirname(__file__), "theme/static"),
            ui_modules={"Transaction": TxModule},
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=options.debug,  # Also activates auto reload
            # wallet_servers = wallet_servers
            bismuth_client = bismuth_client
        )
        super(Application, self).__init__(handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        # Common init for every request
        self.app_log = logging.getLogger("tornado.application")
        # print("cookies", self.cookies)
        self.bismuth = self.settings['bismuth_client']


class HomeHandler(BaseHandler):
    async def get(self):
        """
        :return:
        """
        # self.render("home.html", balance="101", wallet_servers=','.join(self.settings['wallet_servers']))
        self.render("home.html", balance="101", wallet_servers='N/A')
        # self.app_log.info("> home")


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


class JsonHandler(BaseHandler):
    async def get(self, command=''):
        """
        :return:
        """
        try:
            json_result = json.dumps(self.bismuth.command(command))
        except Exception as e:
            json_result = json.dumps(str(e))
        self.write(json_result)
        self.set_header('Content-Type', 'application/json')
        # self.render("home.html", balance="json", wallet_servers=json_result)


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
