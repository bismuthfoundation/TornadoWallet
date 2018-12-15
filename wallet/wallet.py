"""
Proof of concept Python/HTML Wallet for Bismuth, Tornado based

Use --help command line switch to get usage.
"""

import os.path
# import re
import json
import logging
# import random
import string
# import time
# import datetime
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.locks
import tornado.options
import tornado.web
# import unicodedata
import subprocess
import webbrowser
import sys
import socket

from tornado.options import define, options
# from bismuthclient import bismuthapi
from bismuthclient import bismuthclient
from bismuthclient.bismuthutil import BismuthUtil
from modules.basehandlers import BaseHandler, CrystalLoader
from modules import helpers
from modules.crystals import CrystalManager

__version__ = '0.0.67'

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="debug mode", type=bool)
define("verbose", default=False, help="verbose mode", type=bool)
define("theme", default='themes/material', help="theme directory, relative to the app", type=str)
define("server", default='', help="Force a specific wallet server (ip:port)", type=str)
define("crystals", default=False, help="Load Crystals (Experimental)", type=bool)

# Where the wallets and other potential private info are to be stored.
# It's a dir under the user's own home directory.
BISMUTH_PRIVATE_DIR = 'bismuth-private'


class Application(tornado.web.Application):
    def __init__(self):
        # wallet_servers = bismuthapi.get_wallet_servers_legacy()
        servers = None
        if options.server:
            servers = [options.server]
        bismuth_client = bismuthclient.BismuthClient(verbose=options.verbose, servers_list=servers)
        wallet_dir = bismuth_client.user_subdir(BISMUTH_PRIVATE_DIR)
        print("Please store your wallets under '{}'".format(wallet_dir))
        bismuth_client.get_server()
        # Convert relative to absolute
        options.theme = os.path.join(helpers.base_path(), options.theme)
        static_path = os.path.join(options.theme, 'static')
        handlers = [
            (r"/", HomeHandler),
            (r"/transactions/(.*)", TransactionsHandler),
            (r"/json/(.*)", JsonHandler),
            (r"/address/(.*)", AddressHandler),
            (r"/messages/(.*)", AddressHandler),
            (r"/wallet/(.*)", WalletHandler),
            (r"/about/(.*)", AboutHandler),
            (r"/tokens/(.*)", TokensHandler),
            (r"/search/(.*)", SearchHandler),
            (r"/crystals/(.*)", CrystalsHandler),
            (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler,
             dict(path=static_path))
        ]
        # Parse crystals dir, import and plug handlers.
        self.crystals_manager = CrystalManager(init=options.crystals)
        handlers.extend(self.crystals_manager.get_handlers())
        # print("handlers", handlers)
        self.crystals_manager.execute_action_hook('init')

        settings = dict(
            app_title=u"Tornado Bismuth Wallet",
            # template_loader = CrystalLoader(options.theme),
            template_path=os.path.join(os.path.dirname(__file__), options.theme),
            static_path=os.path.join(os.path.dirname(__file__), static_path),
            ui_modules={"Transaction": TxModule},
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            compress_response=True,
            debug=options.debug,  # Also activates auto reload
            serve_traceback=options.debug,
            # wallet_servers = wallet_servers
            bismuth_client = bismuth_client,
            bismuth_vars = {'wallet_version': __version__},
            bismuth_crystals = {}
        )
        super(Application, self).__init__(handlers, **settings)


class HomeHandler(BaseHandler):
    async def get(self):
        """
        :return:
        """
        # self.render("home.html", balance="101", wallet_servers=','.join(self.settings['wallet_servers']))
        if not self.bismuth_vars['address']:
            self.bismuth_vars['address'] = 'None'
            self.redirect("/wallet/load")
            return
        self.bismuth_vars['transactions'] = self.bismuth.latest_transactions(5, for_display=True)
        home_crystals = {"address": self.bismuth_vars['address'], "content": b'',
                         'request_handler': self, "extra": self.bismuth_vars['extra']}
        self.application.crystals_manager.execute_filter_hook('home', home_crystals, first_only=False)
        self.bismuth_vars['extra'] = home_crystals['extra']
        self.render("home.html", bismuth=self.bismuth_vars, home_crystals=home_crystals)
        # self.app_log.info("> home")


class TransactionsHandler(BaseHandler):

    """
    def randhex(self, size):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=size))
    """

    async def send(self, params=None):
        query_params = self.extract_params()
        # print(params)
        _ = self.locale.translate
        self.settings["page_title"] = _("Send BIS")

        if not self.bismuth_vars['address']:
            await self.message(_("Error:")+" "+_("No Wallet"), _("Load your wallet first"), "danger")
            return
        # print(self.bismuth.wallet())
        if self.bismuth.wallet()['encrypted']:
            self.message(_("Error:")+" "+_("Encrypted wallet"), _("You have to unlock your wallet first"), "danger")
            return
        if query_params.get('recipient', False):
            # We have an address param, it's a confirmation
            self.settings["page_title"] = _("Send BIS: Confirmation")
            type='warning'  # Do not translate
            title=_("Please confirm this transaction")
            message=_("Check this is what you intended to do and hit the \"confirm\" button")
            # TODO: address ok?
            # todo: amount ok
            # todo: enough balance?
            self.render("transactions_send_confirm.html", bismuth=self.bismuth_vars, type=type, title=title,
                        message=message)
        else:
            self.render("transactions_send.html", bismuth=self.bismuth_vars)

    async def sendpop(self, params=None):
        # TODO: factorize, common code with send.
        query_params = self.extract_params()
        # print(params)
        _ = self.locale.translate
        self.settings["page_title"] = _("Send BIS")

        if not self.bismuth_vars['address']:
            await self.message(_("Error:")+" "+_("No Wallet"), _("Load your wallet first"), "danger")
            return
        # print(self.bismuth.wallet())
        if self.bismuth.wallet()['encrypted']:
            self.message(_("Error:")+" "+_("Encrypted wallet"), _("You have to unlock your wallet first"), "danger")
            return
        if query_params.get('recipient', False):
            # We have an address param, it's a confirmation
            self.settings["page_title"] = _("Send BIS: Confirmation")
            type='warning'  # Do not translate
            title=_("Please confirm this transaction")
            message=_("Check this is what you intended to do and hit the \"confirm\" button")
            # TODO: address ok?
            # todo: amount ok
            # todo: enough balance?
            self.render("transactions_sendpop_confirm.html", bismuth=self.bismuth_vars, type=type, title=title,
                        message=message)
        else:
            self.message(_("Error:"), "No recipient", "warning")

    async def confirmpop(self, params=None):
        _ = self.locale.translate
        amount = float(self.get_argument("amount"))
        recipient = self.get_argument("recipient")
        data = self.get_argument("data", '')
        operation = self.get_argument("operation", '')
        txid = self.bismuth.send(recipient, amount, operation, data)
        print("txid", txid)
        if txid:
            message = _("Success:") + " " + _("Transaction sent") + "<br>" +\
                         _("The transaction was submitted to the mempool.")\
                         + "<br />" +\
                         _("Txid is {}").format(_(txid))
            color = "success"
            title = _("Success")

        else:
            message =  _("There was an error submitting to the mempool, transaction was not sent.")
            color = "danger"
            title = _("Error")

        self.render("transactions_confirmpop.html", bismuth=self.bismuth_vars, message=message, color=color, title=title)

    async def confirm(self, params=None):
        _ = self.locale.translate
        amount = float(self.get_argument("amount"))
        recipient = self.get_argument("recipient")
        data = self.get_argument("data", '')
        operation = self.get_argument("operation", '')
        txid = self.bismuth.send(recipient, amount, operation, data)
        print("txid", txid)
        if txid:
            self.message(_("Success:") + " " + _("Transaction sent"),
                         _("The transaction was submitted to the mempool.")
                         + "<br />" +
                         _("Txid is {}").format(_(txid)), "success")
        else:
            self.message(_("Error:"), _("There was an error submitting to the mempool, transaction was not sent."), "warning")

    async def receive(self, params=None):
        query_params = self.extract_params()
        address = self.bismuth_vars['server']['address']
        _ = self.locale.translate
        self.settings["page_title"] = _("Receive BIS")
        bisurl = ''
        if query_params.get('address', False):
            address = query_params['address']
            bisurl = BismuthUtil.create_bis_url(address, query_params['amount'], '', query_params['data'])
        self.render("transactions_receive.html", bismuth=self.bismuth_vars, address=address, bisurl=bisurl)

    async def get(self, command=''):
        """
        :return:
        """
        command, *params = command.split('/')
        if command:
            await getattr(self, command)(params)
        else:
            _ = self.locale.translate
            self.settings["page_title"] = _("Transaction list")
            self.bismuth_vars['transactions'] = self.bismuth.latest_transactions(10, for_display=True)
            self.render("transactions.html", bismuth=self.bismuth_vars)

    async def post(self, command=''):
        """
        :return:
        """
        command, *params = command.split('/')
        if command:
            await getattr(self, command)(params)


class JsonHandler(BaseHandler):
    async def get(self, command=''):
        """
        :return:
        """
        params = None
        if '/' in command:
            command, *params = command.split('/')
        # have a list of valid commands for the bismuthclient, and route some to our internal vars
        # The list could also enforce the required number of params.
        if command.startswith('bismuth.'):
            # internal var wallet, config, ....
            command, var = command.split('.')
            json_result = json.dumps(self.bismuth_vars.get(var, None))
        elif command.startswith('settings.'):
            # internal var wallet, config, ....
            command, var = command.split('.')
            json_result = json.dumps(self.settings.get(var, None))
        # TODO: add slug. for crystals
        else:
            try:
                json_result = json.dumps(self.bismuth.command(command, params))
            except Exception as e:
                json_result = json.dumps(str(e))
                # TODO: wrap in a common "error" json structure
        self.write(json_result)
        self.set_header('Content-Type', 'application/json')
        # self.render("home.html", balance="json", wallet_servers=json_result)
        self.finish()


class WalletHandler(BaseHandler):
    """Wallet related routes"""
    async def load(self, params=None):
        if not params:
            wallet_dir = self.bismuth.user_subdir(BISMUTH_PRIVATE_DIR)
            wallets = self.bismuth.list_wallets(wallet_dir)
            self.render("wallet_load.html", wallets=wallets, bismuth=self.bismuth_vars, wallet_dir=wallet_dir)
        else:
            # load a wallet
            file_name = '/'.join(params)
            self.bismuth.load_wallet(file_name)
            # TODO: store as cookie
            self.set_cookie('wallet', file_name)
            self.redirect("/wallet/info")

    async def info(self, params=None):
        wallet_info = self.bismuth.wallet()
        self.render("wallet_info.html", wallet=wallet_info, bismuth=self.bismuth_vars)

    async def create(self, params=None):
        # self.write(json.dumps(self.request))
        _, param = self.request.uri.split("?")
        _ = self.locale.translate
        wallet = param.replace('wallet=', '')
        wallet = wallet.replace('.der', '')  # just in case the user added .der
        wallet_dir = self.bismuth.user_subdir(BISMUTH_PRIVATE_DIR)
        file_name = os.path.join(wallet_dir,'{}.der'.format(wallet))
        if os.path.isfile(file_name):
            self.render("message.html", type="warning", title=_("Error"), message=_("This file already exists: {}.der").format(wallet), bismuth=self.bismuth_vars)
        else:
            # create one
            if self.bismuth.new_wallet(file_name):
                # load the new wallet
                self.bismuth.load_wallet(file_name)
                self.set_cookie('wallet', file_name)
                self.redirect("/wallet/info")
            else:
                self.render("message.html", type="warning", title=_("Error"), message=_("Error creating {}.der").format(wallet), bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        await getattr(self, command)(params)


class AboutHandler(BaseHandler):

    async def credits(self, params=None):
        self.render("about_credits.html", bismuth=self.bismuth_vars)

    async def network(self, params=None):
        self.render("about_network.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'credits'
        await getattr(self, command)(params)


class TokensHandler(BaseHandler):
    """Handler for tokens related features"""

    async def list(self, params=None):
        self.render("tokens_list.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'list'
        await getattr(self, command)(params)


class CrystalsHandler(BaseHandler):

    async def list(self, params=None):
        crystals = self.application.crystals_manager.get_loaded_crystals()
        #crystal_names = {name: name.split('_')[1] for name in crystals.keys()}
        crystal_names = [name.split('_')[1] for name in crystals.keys()]
        self.render("crystals_list.html", bismuth=self.bismuth_vars, crystals=crystal_names)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'list'
        await getattr(self, command)(params)


class AddressHandler(BaseHandler):

    async def get(self, command=''):
        self.render("wip.html", bismuth=self.bismuth_vars)


class SearchHandler(BaseHandler):

    async def get(self, command=''):
        self.render("wip.html", bismuth=self.bismuth_vars)


class MessagesHandler(BaseHandler):

    async def get(self, command=''):
        self.render("wip.html", bismuth=self.bismuth_vars)


class TxModule(tornado.web.UIModule):
    def render(self, tx):
        return self.render_string("modules/transaction.html", tx=tx)


def open_url(url):
    """Opens the default browser with our page"""
    if sys.platform == 'darwin':
        # in case of OS X
        subprocess.Popen(['open', url])
    else:
        webbrowser.open_new_tab(url)


async def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    # In this demo the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    shutdown_event = tornado.locks.Event()
    if not options.debug:
        # In debug mode, any code change will restart the server and launch another tab.
        # This goes in the way, so we deactivate in debug.
        open_url("http://127.0.0.1:{}".format(options.port))
    await shutdown_event.wait()

def port_in_use(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    return result == 0


if __name__ == "__main__":
    if port_in_use(options.port):
        open_url("http://127.0.0.1:{}".format(options.port))
    else:
        # See http://www.lexev.org/en/2015/tornado-internationalization-and-localization/
        locale_path = os.path.join(helpers.base_path(), 'locale')
        tornado.locale.load_gettext_translations(locale_path, 'messages')
        tornado.ioloop.IOLoop.current().run_sync(main)
