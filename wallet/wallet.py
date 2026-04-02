"""
Proof of concept Python/HTML Wallet for Bismuth, Tornado based

Use --help command line switch to get usage.
"""

import os.path

# import re
import json

# import logging
# import random
# import string

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
import threading
import asyncio

from tornado.options import define, options

# from bismuthclient import bismuthapi
from bismuthclient import bismuthclient
from bismuthclient.bismuthutil import BismuthUtil
from modules.basehandlers import BaseHandler, CrystalLoader
from modules import helpers
from modules.crystals import CrystalManager
from modules import i18n  # helps pyinstaller, do not remove

__version__ = "0.1.48"
SHUTDOWN_EVENT = None
SERVER_IOLOOP = None
MACOS_APP = False
DEFAULT_API_PORT = 5658

define("port", default=8888, help="run on the given port", type=int)
define(
    "listen",
    default="127.0.0.1",
    help="What address to listen on, locked by default to localhost for safety",
    type=str,
)
define("debug", default=False, help="debug mode", type=bool)
define("verbose", default=False, help="verbose mode", type=bool)
define(
    "theme",
    default="themes/material",
    help="theme directory, relative to the app",
    type=str,
)
define("server", default="", help="Force a specific wallet server (ip:port)", type=str)
define("crystals", default=True, help="Load Crystals", type=bool)
define("lang", default="", help="Force a language: en,nl,ru...", type=str)
define("maxa", default=10, help="maxa", type=int)
define("romode", default=False, help="Read Only Mode - WIP", type=bool)
define("nowallet", default=False, help="No Wallet Mode - WIP, do NOT use yet", type=bool)
define("missing_address_route", default="/wallet/info", help="Route when no address is defined", type=str)
define("app_title", default=u"Tornado Bismuth Wallet", help="Custom app title", type=str)


def load_app_options(filename):
    if not os.path.isfile(filename):
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as e:
        print("Could not load app options {}: {}".format(filename, e))
    return {}


def save_app_options(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def normalize_api_server(server, port):
    server = (server or "").strip()
    port = str(port or "").strip()
    if not server:
        return {"server": "", "port": "", "ipport": ""}
    if ":" in server and not port:
        server, port = server.rsplit(":", 1)
        server = server.strip()
        port = port.strip()
    if not port:
        port = str(DEFAULT_API_PORT)
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        raise ValueError("Port must be a valid number.")
    if port_int < 1 or port_int > 65535:
        raise ValueError("Port must be between 1 and 65535.")
    if not server:
        raise ValueError("Server must not be empty.")
    return {"server": server, "port": str(port_int), "ipport": "{}:{}".format(server, port_int)}


# Decorator to limit available methods when in read only mode
def write_protected(func):
    async def decorator(obj, *args, **kwargs):
        _ = obj.locale.translate
        if obj.ro_mode:
            obj.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Read only mode, command is not allowed"),
                bismuth=obj.bismuth_vars,
            )
            return
        await func(obj, *args, **kwargs)
    return decorator


class Application(tornado.web.Application):
    def __init__(self):
        # wallet_servers = bismuthapi.get_wallet_servers_legacy()
        wallet_dir = helpers.get_private_dir()
        self.wallet_dir = wallet_dir
        self.options_file = os.path.join(wallet_dir, "options.json")
        self.app_options = load_app_options(self.options_file)
        self.custom_api = {"server": "", "port": "", "ipport": ""}
        servers = None
        if options.server:
            self.custom_api = normalize_api_server(options.server, "")
            servers = [self.custom_api["ipport"]]
        else:
            try:
                self.custom_api = normalize_api_server(
                    self.app_options.get("custom_api_server", ""),
                    self.app_options.get("custom_api_port", ""),
                )
            except ValueError:
                self.custom_api = {"server": "", "port": "", "ipport": ""}
            if self.custom_api["ipport"]:
                servers = [self.custom_api["ipport"]]
        bismuth_client = bismuthclient.BismuthClient(
            verbose=options.verbose, servers_list=servers
        )
        self.wallet_settings = None
        print("Please store your wallets under '{}'".format(wallet_dir))
        if options.romode:
            print("Read only mode")
        # self.load_user_data("{}/options.json".format(wallet_dir))
        if options.nowallet:
            print("No Wallet mode")
            bismuth_client.wallet_file = None
            bismuth_client.address = 'FakeAddressMode'
        else:
            bismuth_client.load_multi_wallet("{}/wallet.json".format(wallet_dir))
        bismuth_client.set_alias_cache_file("{}/alias_cache.json".format(wallet_dir))
        # Convert relative to absolute
        options.theme = os.path.join(helpers.base_path(), options.theme)
        static_path = os.path.join(options.theme, "static")
        common_path = os.path.join(helpers.base_path(), "themes/common")
        self.default_handlers = [
            (r"/", HomeHandler),
            (r"/transactions/(.*)", TransactionsHandler),
            (r"/json/(.*)", JsonHandler),
            (r"/address/(.*)", AddressHandler),
            (r"/messages/(.*)", MessagesHandler),
            (r"/wallet/(.*)", WalletHandler),
            (r"/about/(.*)", AboutHandler),
            (r"/tokens/(.*)", TokensHandler),
            (r"/search/(.*)", SearchHandler),
            (r"/crystals/(.*)", CrystalsHandler),
            (r"/tools/(.*)", ToolsHandler),
            (
                r"/(apple-touch-icon\.png)",
                tornado.web.StaticFileHandler,
                dict(path=static_path),
            ),
            (r'/common/(.*)', tornado.web.StaticFileHandler, {'path': common_path}),
        ]
        # Parse crystals dir, import and plug handlers.
        self.crystals_manager = CrystalManager(init=options.crystals)
        handlers = self.default_handlers.copy()
        handlers.extend(self.crystals_manager.get_handlers())
        # print("handlers", handlers)
        self.crystals_manager.execute_action_hook("init")

        settings = dict(
            app_title=options.app_title,
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
            max_addresses=options.maxa,
            lang=options.lang,
            ro_mode=options.romode,
            # wallet_servers = wallet_servers
            bismuth_client=bismuth_client,
            custom_api=self.custom_api,
            bismuth_vars={
                "wallet_version": __version__,
                "bismuthclient_version": bismuthclient.__version__,
            },
            bismuth_crystals={},
        )
        super(Application, self).__init__(handlers, **settings)
        self._server_connect_thread = None
        self._server_connect_lock = threading.Lock()
        self.connect_server_async(force=True)

    def set_custom_api(self, server, port):
        custom_api = normalize_api_server(server, port)
        self.custom_api = custom_api
        self.settings["custom_api"] = custom_api
        self.app_options["custom_api_server"] = custom_api["server"]
        self.app_options["custom_api_port"] = custom_api["port"]
        save_app_options(self.options_file, self.app_options)
        client = self.settings["bismuth_client"]
        client.initial_servers_list = [custom_api["ipport"]] if custom_api["ipport"] else []
        client.servers_list = list(client.initial_servers_list)
        client.full_servers_list = (
            [{"ip": custom_api["server"], "port": custom_api["port"], "load": "N/A", "height": "N/A"}]
            if custom_api["ipport"]
            else []
        )
        client._current_server = None
        client._connection = None
        client.clear_cache()
        return custom_api

    def clear_custom_api(self):
        self.custom_api = {"server": "", "port": "", "ipport": ""}
        self.settings["custom_api"] = self.custom_api
        self.app_options["custom_api_server"] = ""
        self.app_options["custom_api_port"] = ""
        save_app_options(self.options_file, self.app_options)
        client = self.settings["bismuth_client"]
        client.initial_servers_list = []
        client.servers_list = []
        client.full_servers_list = []
        client._current_server = None
        client._connection = None
        client.clear_cache()

    def connect_server_async(self, force=False):
        with self._server_connect_lock:
            if (
                not force
                and self._server_connect_thread
                and self._server_connect_thread.is_alive()
            ):
                return

            def worker():
                try:
                    client = self.settings["bismuth_client"]
                    client.get_server()
                    if client._current_server and not client.initial_servers_list:
                        try:
                            client.refresh_server_list()
                        except Exception as e:
                            print("Background server list refresh failed: {}".format(e))
                    client.clear_cache()
                except Exception as e:
                    print("Background server connection failed: {}".format(e))

            self._server_connect_thread = threading.Thread(
                target=worker, name="wallet-server-connect", daemon=True
            )
            self._server_connect_thread.start()

    def wait_for_initial_server(self, timeout=4.0):
        thread = self._server_connect_thread
        if thread and thread.is_alive():
            thread.join(timeout=timeout)

    def load_user_data(self, filename: str):
        """User data is config + optional integrated wallets."""
        # TODO: no, already in wallet.
        raise RuntimeError("Deprecated, do not use")
        """
        if not os.path.isfile(filename):
            default = {"spend": {"type": None, "value": None}, "version": __version__}
            with open(filename, 'w') as f:
                json.dump(default, f)
            self.wallet_settings = default
        else:
            with open(filename) as f:
                self.wallet_settings = json.load(f)
        """


class HomeHandler(BaseHandler):
    async def get(self):
        """
        :return:
        """
        # self.render("home.html", balance="101", wallet_servers=','.join(self.settings['wallet_servers']))
        if not self.bismuth_vars["address"]:
            self.bismuth_vars["address"] = "None"
            # self.redirect("/wallet/info")
            self.redirect(options.missing_address_route)
            return
        try:
            self.bismuth_vars["transactions"] = self.bismuth.latest_transactions(
                5, for_display=True, mempool_included=True
            )
        except Exception:
            self.bismuth_vars["transactions"] = []
        home_crystals = {
            "address": self.bismuth_vars["address"],
            "content": b"",
            "request_handler": self,
            "extra": self.bismuth_vars["extra"],
        }
        self.application.crystals_manager.execute_filter_hook(
            "home", home_crystals, first_only=False
        )
        self.bismuth_vars["extra"] = home_crystals["extra"]
        self.bismuth_vars["news"] = helpers.get_news()
        self.render("home.html", bismuth=self.bismuth_vars, home_crystals=home_crystals)
        # self.app_log.info("> home")


class TransactionsHandler(BaseHandler):
    """
    def randhex(self, size):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=size))
    """
    @write_protected
    async def send(self, params=None):
        _ = self.locale.translate
        # query_params = self.extract_params()
        # print(params)
        self.settings["page_title"] = _("Send BIS")
        if not self.bismuth_vars["address"]:
            await self.message(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        # print(self.bismuth.wallet())
        if self.bismuth._wallet._locked:
            self.message(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        # if query_params.get('recipient', False):
        if self.get_argument("recipient", False):
            # We have an address param, it's a confirmation
            self.settings["page_title"] = _("Send BIS: Confirmation")
            type = "warning"  # Do not translate
            title = _("Please confirm this transaction")
            message = _(
                'Check this is what you intended to do and hit the "confirm" button'
            )

            if self.get_argument(
                "data", ""
            ) == "" and self.bismuth.reject_empty_message_for(
                self.get_argument("recipient")
            ):
                await self.message(
                    _("Error:") + " " + _("No message"),
                    _("Sending to this recipient needs a proper message"),
                    "danger",
                )
                return

            # TODO: address ok?
            # todo: amount ok
            # todo: enough balance?
            self.render(
                "transactions_send_confirm.html",
                bismuth=self.bismuth_vars,
                type=type,
                title=title,
                message=message,
            )
        else:
            self.render("transactions_send.html", bismuth=self.bismuth_vars)

    @write_protected
    async def send_pop(self, params=None):
        # TODO: factorize, common code with send.
        _ = self.locale.translate
        self.settings["page_title"] = _("Send BIS")

        if not self.bismuth_vars["address"]:
            await self.message(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        # print(self.bismuth.wallet())
        if self.bismuth._wallet._locked:
            self.message(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        if self.get_argument("url", False):
            # print("url", self.get_argument('url'))
            # We have an url param, confirm once decoded
            self.settings["page_title"] = _("Send BIS: Confirmation")
            type = "warning"  # Do not translate
            title = _("Please confirm this transaction")
            message = _(
                'Check this is what you intended to do and hit the "confirm" button'
            )
            # self.bismuth_vars['recipient'] operation data amount
            decoded = BismuthUtil.read_url(self.get_argument("url"))
            if decoded.get("Error", False):
                self.message_pop(_("Error:"), _(decoded["Error"]), "warning")
                return
            # print(decoded)
            self.bismuth_vars["params"]["recipient"] = decoded["recipient"]
            # TODO: verify the sender address is a correct one
            # address ok?
            if not BismuthUtil.valid_address(self.bismuth_vars["params"]["recipient"]):
                await self.message_pop(
                    _("Error:") + " " + _("Bad address"),
                    _("Recipient address '{}' seems invalid").format(self.bismuth_vars["params"]["recipient"]),
                    "warning",
                )
                return
            self.bismuth_vars["params"]["amount"] = decoded["amount"]
            self.bismuth_vars["params"]["operation"] = decoded["operation"]
            self.bismuth_vars["params"]["data"] = decoded["openfield"]
            if self.bismuth_vars["params"][
                "data"
            ] == "" and self.bismuth.reject_empty_message_for(
                self.bismuth_vars["params"]["recipient"]
            ):
                await self.message_pop(
                    _("Error:") + " " + _("No message"),
                    _("Sending to this recipient needs a proper message"),
                    "danger",
                )
                return
            # todo: amount ok
            # todo: enough balance?
            self.render(
                "transactions_sendpop_confirm.html",
                bismuth=self.bismuth_vars,
                type=type,
                title=title,
                message=message,
            )
        elif self.get_argument("recipient", False):
            # We have an address param, it's a confirmation
            self.settings["page_title"] = _("Send BIS: Confirmation")
            type = "warning"  # Do not translate
            title = _("Please confirm this transaction")
            message = _(
                'Check this is what you intended to do and hit the "confirm" button'
            )

            self.bismuth_vars["params"]["recipient"] = self.get_argument("recipient")
            self.bismuth_vars["params"]["amount"] = self.get_argument(
                "amount", "0.00000000"
            )
            self.bismuth_vars["params"]["operation"] = self.get_argument(
                "operation", ""
            )
            self.bismuth_vars["params"]["data"] = self.get_argument("data", "")
            if self.bismuth_vars["params"][
                "data"
            ] == "" and self.bismuth.reject_empty_message_for(
                self.bismuth_vars["params"]["recipient"]
            ):
                await self.message_pop(
                    _("Error:") + " " + _("No message"),
                    _("Sending to this recipient needs a proper message"),
                    "danger",
                )
                return
            # address ok?
            if not BismuthUtil.valid_address(self.bismuth_vars["params"]["recipient"]):
                await self.message_pop(
                    _("Error:") + " " + _("Bad address"),
                    _("Recipient address '{}' seems invalid").format(self.bismuth_vars["params"]["recipient"]),
                    "warning",
                )
                return
            # todo: amount ok
            # todo: enough balance?
            self.render(
                "transactions_sendpop_confirm.html",
                bismuth=self.bismuth_vars,
                type=type,
                title=title,
                message=message,
            )
        else:
            self.message(_("Error:"), "No recipient", "warning")

    @write_protected
    async def confirmpop(self, params=None):
        _ = self.locale.translate
        spend_token = self.get_argument(
            "token", ""
        )  # Beware naming inconsistencies token, spend_token
        if not self.bismuth_vars["address"]:
            await self.message_pop(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        if self.bismuth._wallet._locked:
            self.message_pop(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        # check spend protection
        # TODO: add more methods
        if self.bismuth.wallet()["spend"]["type"] == "PIN":
            # print(spend_token, self.bismuth.wallet()['spend'])
            if spend_token != self.bismuth.wallet()["spend"]["value"]:
                self.message_pop(
                    _("Error:") + " " + _("Spend protection"),
                    _("Invalid PIN Number"),
                    "warning",
                )
                return
        amount = float(self.get_argument("amount"))
        recipient = self.get_argument("recipient")
        data = self.get_argument("data", "")
        operation = self.get_argument("operation", "")
        reply = list()
        txid = self.bismuth.send(recipient, amount, operation, data, reply)
        # print("txidpop", txid)
        if txid:
            message = (
                _("Success:")
                + " "
                + _("Transaction sent")
                + "<br>"
                + _("The transaction was submitted to the mempool.")
                + "<br />"
                + _("Txid is {}").format(_(txid))
            )
            color = "success"
            title = _("Success")

        else:
            message = _(
                "There was an error submitting to the mempool, transaction was not sent."
            )
            message += "<br />"
            message += ",".join(reply)
            color = "danger"
            title = _("Error")
        self.render(
            "transactions_confirmpop.html",
            bismuth=self.bismuth_vars,
            message=message,
            color=color,
            title=title,
        )

    @write_protected
    async def confirm(self, params=None):
        _ = self.locale.translate
        spend_token = self.get_argument(
            "token", ""
        )  # Beware naming inconsistencies token, spend_token
        if not self.bismuth_vars["address"]:
            await self.message_pop(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        if self.bismuth._wallet._locked:
            self.message_pop(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        # check spend protection
        # TODO: add more methods
        if self.bismuth.wallet()["spend"]["type"] == "PIN":
            # print(spend_token, self.bismuth.wallet()['spend'])
            if spend_token != self.bismuth.wallet()["spend"]["value"]:
                self.message_pop(
                    _("Error:") + " " + _("Spend protection"),
                    _("Invalid PIN Number"),
                    "warning",
                )
                return
        amount = float(self.get_argument("amount"))
        recipient = self.get_argument("recipient")
        data = self.get_argument("data", "")
        operation = self.get_argument("operation", "")
        txid = self.bismuth.send(recipient, amount, operation, data)
        # print("txid1", txid)
        if txid:
            self.message(
                _("Success:") + " " + _("Transaction sent"),
                _("The transaction was submitted to the mempool.")
                + "<br />"
                + _("Txid is {}").format(_(txid)),
                "success",
            )
        else:
            self.message(
                _("Error:"),
                _(
                    "There was an error submitting to the mempool, transaction was not sent."
                ),
                "warning",
            )

    async def receive(self, params=None):
        _ = self.locale.translate
        if not self.bismuth_vars["address"]:
            await self.message(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        # print(self.bismuth.wallet())
        if self.bismuth._wallet._locked:
            self.message(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        address = self.bismuth_vars["server"]["address"]
        self.settings["page_title"] = _("Receive BIS")
        bisurl = ""
        # print("address", self.get_query_argument('address', 'no'))
        if self.get_query_argument("address", False):
            address = self.get_query_argument("address")
            amount = "{:0.8f}".format(float(self.get_query_argument("amount", 0)))
            data = self.get_query_argument("data", "")
            self.bismuth_vars["params"]["address"] = address
            self.bismuth_vars["params"]["amount"] = amount
            self.bismuth_vars["params"]["data"] = data
            bisurl = BismuthUtil.create_bis_url(address, amount, "", data)
        self.render(
            "transactions_receive.html",
            bismuth=self.bismuth_vars,
            address=address,
            bisurl=bisurl,
        )

    async def get(self, command=""):
        """
        :return:
        """
        command, *params = command.split("/")
        if command:
            await getattr(self, command)(params)
        else:
            start = int(self.get_query_argument("start", 0))
            count = int(self.get_query_argument("count", 10))
            if count > 50:
                count = 50
            _ = self.locale.translate
            self.settings["page_title"] = _("Transaction list")
            self.bismuth_vars["transactions"] = self.bismuth.latest_transactions(
                count, offset=start, for_display=True, mempool_included=True
            )
            addresses = set()
            for tx in self.bismuth_vars["transactions"]:
                addresses.update([tx["recipient"], tx["address"]])
            aliases = self.bismuth.get_aliases_of(addresses)
            self.bismuth_vars["aliases"] = aliases
            self.render(
                "transactions.html",
                bismuth=self.bismuth_vars,
                offset=start,
                count=count,
            )

    async def post(self, command=""):
        """
        :return:
        """
        command, *params = command.split("/")
        if command:
            await getattr(self, command)(params)


class JsonHandler(BaseHandler):
    async def get(self, command=""):
        """
        :return:
        """
        params = None
        if "/" in command:
            command, *params = command.split("/")
        # have a list of valid commands for the bismuthclient, and route some to our internal vars
        # The list could also enforce the required number of params.
        if command.startswith("bismuth."):
            # internal var wallet, config, ....
            command, var = command.split(".")
            json_result = json.dumps(self.bismuth_vars.get(var, None))
        elif command.startswith("settings."):
            # internal var wallet, config, ....
            command, var = command.split(".")
            json_result = json.dumps(self.settings.get(var, None))
        # TODO: add slug. for crystals
        else:
            try:
                json_result = json.dumps(self.bismuth.command(command, params))
            except Exception as e:
                json_result = json.dumps(str(e))
                # TODO: wrap in a common "error" json structure
        self.write(json_result)
        self.set_header("Content-Type", "application/json")
        # self.render("home.html", balance="json", wallet_servers=json_result)
        self.finish()


class WalletHandler(BaseHandler):
    """Wallet related routes"""

    async def load(self, params=None, post=False):
        _ = self.locale.translate
        if self.bismuth._wallet._locked:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("You have to unlock your wallet first"),
                bismuth=self.bismuth_vars,
            )
        global_balance = _("Click")
        if "global" in params:
            # Ask the global balance
            try:
                global_balance = self.bismuth.global_balance(for_display=True)
            except Exception as e:
                self.app_log.warning("Exception {} global balance".format(e))
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Time out, please try reloading").format(e),
                    bismuth=self.bismuth_vars,
                )
                return

        wallet_dir = helpers.get_private_dir()
        # This lists the old style wallets
        wallets = self.bismuth.list_wallets(wallet_dir)
        # TODO: fix private access
        addresses = self.bismuth._wallet._addresses
        if "detail" in params:
            # get balance of every address
            balances = self.bismuth.all_balances(for_display=True)
            self.render(
                "wallet_load_detail.html",
                wallets=wallets,
                bismuth=self.bismuth_vars,
                wallet_dir=wallet_dir,
                global_balance=global_balance,
                balances=balances,
                addresses=addresses,
            )
        else:
            self.render(
                "wallet_load.html",
                wallets=wallets,
                bismuth=self.bismuth_vars,
                wallet_dir=wallet_dir,
                global_balance=global_balance,
                addresses=addresses,
            )

    async def load_address(self, params=None, post=False):
        """Set an address from the multiwallet as current address"""
        _ = self.locale.translate
        address = params[0]
        try:
            self.bismuth.set_address(address)
        except Exception as e:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error: {}").format(e),
                bismuth=self.bismuth_vars,
            )
            return
        self.set_cookie("address", address)
        self.redirect("/wallet/load")

    async def info(self, params=None, post=False):
        wallet_info = self.bismuth.wallet()
        # self.bismuth_vars['spend_type']['type'] = 'YUBICO'
        self.render("wallet_info.html", wallet=wallet_info, bismuth=self.bismuth_vars)

    @write_protected
    async def import_der(self, params=None, post: bool = False):
        _ = self.locale.translate
        if self.bismuth._wallet._locked:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("You have to unlock your wallet first"),
                bismuth=self.bismuth_vars,
            )
        file_name = "/".join(params)
        # print(file_name)
        try:
            self.bismuth._wallet.import_der(wallet_der=file_name)
        except Exception as e:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error: {}").format(e),
                bismuth=self.bismuth_vars,
            )
            return
        self.redirect("/wallet/load")

    @write_protected
    async def import_encrypted_der1(self, params=None, post: bool = False):
        """Ask for pass"""
        _ = self.locale.translate
        if self.bismuth._wallet._locked:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("You have to unlock your wallet first"),
                bismuth=self.bismuth_vars,
            )
        file_name = "/".join(params)
        # print(file_name)
        self.render(
            "wallet_import_encrypted_der1.html",
            wallet_file=file_name,
            bismuth=self.bismuth_vars,
        )

    @write_protected
    async def import_encrypted_der2(self, params=None, post: bool = False):
        """Ask for pass"""
        _ = self.locale.translate
        if not post:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error"),
                bismuth=self.bismuth_vars,
            )
            return
        wallet_file = self.get_argument("wallet_file")
        wallet_password = self.get_argument("wallet_password")
        # print(wallet_file, wallet_password)
        try:
            self.bismuth._wallet.import_der(
                wallet_der=wallet_file, source_password=wallet_password
            )
        except Exception as e:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error: {}").format(e),
                bismuth=self.bismuth_vars,
            )
            return
        self.redirect("/wallet/load")

    @write_protected
    async def import_key(self, params=None, post: bool = False):
        """Check key is good and show address for confirm"""
        _ = self.locale.translate
        if self.bismuth._wallet._locked:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("You have to unlock your wallet first"),
                bismuth=self.bismuth_vars,
            )
            return
        key_type = self.get_argument("key_type", "ECDSA").strip().upper()
        privkey = self.get_argument("privkey").strip()
        label = self.get_argument("label").strip()
        import_confirmation = self.get_argument("import", False)
        # print({ k: self.get_argument(k) for k in self.request.arguments })
        if self.get_argument("cancel", False):
            self.redirect("/wallet/load")
        elif import_confirmation:
            # We confirmed, import for good.
            if key_type == "ED25519":
                self.bismuth._wallet.import_ed25519_pk(privkey, label)
            else:
                self.bismuth._wallet.import_ecdsa_pk(privkey, label)
            self.redirect("/wallet/load")
        else:
            # Ask for confirm
            if key_type == "ED25519":
                signer = self.bismuth._wallet.get_ed25519_key(privkey)
            else:
                signer = self.bismuth._wallet.get_ecdsa_key(privkey)
            address = signer['address']
            pubkey = signer['public_key']
            # print(file_name)
            self.render(
                "wallet_import_ecdsa1.html",
                key_type=key_type,
                privkey=privkey,
                pubkey=pubkey,
                label=label,
                address=address,
                bismuth=self.bismuth_vars,
            )

    @write_protected
    async def create(self, params=None, post: bool = False):
        # self.write(json.dumps(self.request))
        # TODO: DEPRECATED
        _, param = self.request.uri.split("?")
        _ = self.locale.translate
        wallet = param.replace("wallet=", "")
        wallet = wallet.replace(".der", "")  # just in case the user added .der
        wallet_dir = helpers.get_private_dir()
        file_name = os.path.join(wallet_dir, "{}.der".format(wallet))
        if os.path.isfile(file_name):
            self.render(
                "message.htm+l",
                type="warning",
                title=_("Error"),
                message=_("This file already exists: {}.der").format(wallet),
                bismuth=self.bismuth_vars,
            )
        else:
            # create one
            if self.bismuth.new_wallet(file_name):
                # load the new wallet
                self.bismuth.load_wallet(file_name)
                self.set_cookie("wallet", file_name)
                self.redirect("/wallet/info")
            else:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error creating {}.der").format(wallet),
                    bismuth=self.bismuth_vars,
                )

    @write_protected
    async def new_address(self, params=None, post=False):
        """Adds a new address to the current multiwallet."""
        _ = self.locale.translate
        # TODO: config item w/default?
        if len(self.bismuth._wallet._data["addresses"]) >= self.settings["max_addresses"]:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Max of {} addresses reached.").format(self.settings["max_addresses"]),
                bismuth=self.bismuth_vars,
            )
            return
        label = self.get_argument("label", None)
        address_type = self.get_argument("addresstype", "RSA")
        # TODO: check and block if this label already exists?
        try:
            self.bismuth._wallet.new_address(label=label, type=address_type)
            self.redirect("/wallet/load")
        except Exception as e:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error: {}").format(e),
                bismuth=self.bismuth_vars,
            )

    @write_protected
    async def set_label(self, params=None, post=False):
        """Defines or edit the label of an address"""
        _ = self.locale.translate
        label = self.get_argument("label", None)
        address = self.get_argument("address", None)
        # print(address, label, params)
        try:
            self.bismuth._wallet.set_label(address=address, label=label)
            # self.bismuth.clear_cache()
            self.redirect("/wallet/load")
        except Exception as e:
            self.render(
                "message.html",
                type="warning",
                title=_("Error"),
                message=_("Error: {}").format(e),
                bismuth=self.bismuth_vars,
            )

    async def protection(self, params=None, post=False):
        """Set lock, unlock, and other actions"""
        _ = self.locale.translate
        if not post:
            self.redirect("/wallet/info")
            return
        action = self.get_argument("action", None)
        if action == "lock":
            try:
                self.bismuth._wallet.lock()
                # TODO: Clear cache because sensitive info can be there (ex: API answer from crystals, transactions)
            except Exception as e:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error: {}").format(e),
                    bismuth=self.bismuth_vars,
                )
                return
            self.redirect("/wallet/info")
        elif action == "unlock":
            try:
                self.bismuth._wallet.unlock(self.get_argument("master_password", None))
            except Exception as e:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error: {}").format(e),
                    bismuth=self.bismuth_vars,
                )
                return
            self.redirect("/wallet/info")
        elif action == "set_master":
            if self.ro_mode:
                return
            current_password = self.get_argument("master_password", None)
            new_password = self.get_argument("new_master_password", None)
            new_password2 = self.get_argument("new_master_password2", None)
            if new_password != new_password2:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Passwords do not match"),
                    bismuth=self.bismuth_vars,
                )
                return
            try:
                self.bismuth._wallet.encrypt(new_password, current_password)
            except Exception as e:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error: {}").format(e),
                    bismuth=self.bismuth_vars,
                )
                return
            self.redirect("/wallet/info")
        elif action == "set_spend":
            if self.ro_mode:
                return
            password = self.get_argument("master_password", None)
            spend_type = self.get_argument("spend_type", None)
            spend_value = self.get_argument("spend_value", None)
            if spend_type != "None" and spend_value == "":
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error: {}").format(_("PIN code can't be empty")),
                    bismuth=self.bismuth_vars,
                )
                return
            try:
                self.bismuth._wallet.set_spend(
                    spend_type, spend_value, password=password
                )
            except Exception as e:
                self.render(
                    "message.html",
                    type="warning",
                    title=_("Error"),
                    message=_("Error: {}").format(e),
                    bismuth=self.bismuth_vars,
                )
                return
            self.redirect("/wallet/info")
        else:
            self.redirect("/wallet/info")

    async def get(self, command=""):
        command, *params = command.split("/")
        await getattr(self, command)(params)

    async def post(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "list"
        await getattr(self, command)(params, post=True)


class AboutHandler(BaseHandler):
    def refresh_network_servers(self):
        active_servers = []
        try:
            active_servers = helpers.get_active_fallback_wallet_servers()
            if not active_servers:
                active_servers = helpers.get_active_wallet_servers()
        except Exception:
            active_servers = []
        self.bismuth_vars["network_servers"] = active_servers
        if not self.settings.get("custom_api", {}).get("ipport"):
            try:
                if active_servers:
                    self.bismuth.full_servers_list = active_servers
                    self.bismuth.servers_list = [
                        "{}:{}".format(server["ip"], server["port"])
                        for server in active_servers
                    ]
                else:
                    self.bismuth.refresh_server_list()
                    self.bismuth_vars["network_servers"] = self.bismuth.full_servers_list or []
            except Exception:
                pass

    async def connect(self, params=None):
        # self.render("message.html", type="warning", title="WIP", message="WIP", bismuth=self.bismuth_vars)
        # print("params", params)
        _ = self.locale.translate
        server = params[0]
        host, port = server.rsplit(":", 1)
        self.application.set_custom_api(host, port)
        if not self.bismuth.set_server(server):
            self.application.connect_server_async(force=True)
            self.bismuth_vars["network_message"] = {
                "type": "warning",
                "title": _("Network"),
                "message": _("Could not connect to the selected wallet server. The setting was saved."),
            }
        self.refresh_bismuth_state()
        self.render("about_network.html", bismuth=self.bismuth_vars)

    async def refresh(self, params=None):
        _ = self.locale.translate
        self.refresh_network_servers()
        self.application.connect_server_async(force=True)
        self.bismuth_vars["network_message"] = {
            "type": "info",
            "title": _("Network"),
            "message": _("Refreshing wallet server information in the background."),
        }
        self.refresh_bismuth_state()
        self.render("about_network.html", bismuth=self.bismuth_vars)
        """
        self.render("message.html", type="warning", title="WIP", message="WIP",
                    bismuth=self.bismuth_vars)
        """

    async def setlang(self, params=None):
        lang = params[0]
        if lang == "*":
            self.set_cookie("lang", "")
        self.set_cookie("lang", lang)
        self.redirect("/")

    async def credits(self, params=None):
        self.render("about_credits.html", bismuth=self.bismuth_vars)

    async def help(self, params=None):
        self.render("about_help.html", bismuth=self.bismuth_vars)

    async def network(self, params=None, post=False):
        _ = self.locale.translate
        if post:
            action = self.get_body_argument("action", "save")
            try:
                if action == "clear":
                    self.application.clear_custom_api()
                    self.application.connect_server_async(force=True)
                    self.bismuth_vars["network_message"] = {
                        "type": "info",
                        "title": _("Network"),
                        "message": _("Custom wallet server removed. Automatic discovery is enabled again."),
                    }
                else:
                    custom_api = self.application.set_custom_api(
                        self.get_body_argument("api_server", ""),
                        self.get_body_argument("api_port", ""),
                    )
                    self.application.connect_server_async(force=True)
                    self.bismuth_vars["network_message"] = {
                        "type": "success",
                        "title": _("Network"),
                        "message": _("Custom wallet server saved: {}").format(custom_api["ipport"]),
                    }
            except ValueError as e:
                self.bismuth_vars["network_message"] = {
                    "type": "warning",
                    "title": _("Error"),
                    "message": str(e),
                }
            self.refresh_bismuth_state()
        else:
            self.refresh_network_servers()
            self.refresh_bismuth_state()
        self.render("about_network.html", bismuth=self.bismuth_vars)

    async def quit(self, params=None):
        _ = self.locale.translate
        self.render(
            "message.html",
            type="success",
            title=_("Quit"),
            message=_("Tornado Wallet is shutting down."),
            bismuth=self.bismuth_vars,
        )
        tornado.ioloop.IOLoop.current().call_later(0.2, request_shutdown)

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "credits"
        await getattr(self, command)(params)

    async def post(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "network"
        await getattr(self, command)(params, post=True)


class TokensHandler(BaseHandler):
    """Handler for tokens related features"""

    async def list(self, params=None):
        self.render("tokens_list.html", bismuth=self.bismuth_vars)

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "list"
        await getattr(self, command)(params)


class CrystalsHandler(BaseHandler):
    async def list(self, params=None, post=False):
        loaded_crystals = self.application.crystals_manager.get_loaded_crystals()
        available_crystals = self.application.crystals_manager.get_available_crystals()
        # crystal_names = [name.split('_')[1] for name in available_crystals.keys()]
        # crystals = {name.split('_')[1]: name in loaded_crystals for name in available_crystals}
        crystals = {
            name.split("_")[1]: {
                "active": name in loaded_crystals,
                "fullname": name,
                "about": available_crystals[name]["about"],
            }
            for name in available_crystals
        }
        if post:
            new_actives = {
                data["fullname"]: bool(
                    self.get_argument("active_" + data["fullname"], False)
                )
                for data in crystals.values()
            }
            # print("New actives", new_actives)
            added = self.application.crystals_manager.load_crystals(new_actives)
            # print("wild ", self.application.wildcard_router.__dict__)
            # print("def ", self.application.default_router.__dict__)
            current_handlers = [
                rule.target.__name__.replace("Handler", "").lower()
                for rule in self.application.wildcard_router.rules
            ]
            for new in added:
                if new.split("_")[1] not in current_handlers:
                    handler = self.application.crystals_manager.get_handler(new)
                    self.application.add_handlers(r".*", handler)  # match any host
            loaded_crystals = self.application.crystals_manager.get_loaded_crystals()
            self.update_crystals()
            crystals = {
                name.split("_")[1]: {
                    "active": name in loaded_crystals,
                    "fullname": name,
                    "about": available_crystals[name]["about"],
                }
                for name in available_crystals
            }

        self.render("crystals_list.html", bismuth=self.bismuth_vars, crystals=crystals)

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "list"
        await getattr(self, command)(params)

    async def post(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "list"
        await getattr(self, command)(params, post=True)


class AddressHandler(BaseHandler):
    async def get(self, command=""):
        self.render("wip.html", bismuth=self.bismuth_vars)


class SearchHandler(BaseHandler):
    async def get(self, command=""):
        self.render("wip.html", bismuth=self.bismuth_vars)


class MessagesHandler(BaseHandler):
    async def index(self, params=None, post=False):
        self.render("messages.html", bismuth=self.bismuth_vars)

    @write_protected
    async def sign_pop(self, params=None):
        _ = self.locale.translate
        message = self.get_argument("data", "")
        spend_token = self.get_argument(
            "token", ""
        )  # Beware naming inconsistencies token, spend_token
        self.settings["page_title"] = _("Sign message")
        if not self.bismuth_vars["address"]:
            self.message_pop(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        # print(self.bismuth.wallet())
        if self.bismuth._wallet._locked:
            self.message_pop(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        # check spend protection
        # TODO: add more methods
        if self.bismuth.wallet()["spend"]["type"] == "PIN":
            # print(spend_token, self.bismuth.wallet()['spend'])
            if spend_token != self.bismuth.wallet()["spend"]["value"]:
                self.message_pop(
                    _("Error:") + " " + _("Spend protection"),
                    _("Invalid PIN Number"),
                    "warning",
                )
                return
        try:
            data = self.bismuth.sign(message)
        except Exception as e:
            self.message_pop(
                _("Error:"),
                _("Could not sign the message.") + " " + str(e),
                "danger",
            )
            return
        if len(message) > 50:
            message = message[:50] + "[...]"
        message = _("Your message '{}' has been signed.").format(message)
        self.render(
            "messages_pop.html",
            bismuth=self.bismuth_vars,
            title=self.settings["page_title"],
            message=message,
            color="success",
            what=_("Signature"),
            data=data,
        )

    @write_protected
    async def decrypt_pop(self, params=None, post=True):
        _ = self.locale.translate
        message = self.get_argument("data", "")
        spend_token = self.get_argument(
            "token", ""
        )  # Beware naming inconsistencies token, spend_token
        self.settings["page_title"] = _("Decrypt message")
        if not self.bismuth_vars["address"]:
            self.message_pop(
                _("Error:") + " " + _("No Wallet"),
                _("Load your wallet first"),
                "danger",
            )
            return
        # print(self.bismuth.wallet())
        if self.bismuth._wallet._locked:
            self.message_pop(
                _("Error:") + " " + _("Encrypted wallet"),
                _("You have to unlock your wallet first"),
                "danger",
            )
            return
        # check spend protection
        # TODO: add more methods and factorize that code
        if self.bismuth.wallet()["spend"]["type"] == "PIN":
            # print(spend_token, self.bismuth.wallet()['spend'])
            if spend_token != self.bismuth.wallet()["spend"]["value"]:
                self.message_pop(
                    _("Error:") + " " + _("Spend protection"),
                    _("Invalid PIN Number"),
                    "warning",
                )
                return
        try:
            data = self.bismuth.decrypt(message)
        except Exception as e:
            self.message_pop(
                _("Error:"),
                _("Could not decrypt the message.") + " " + str(e),
                "danger",
            )
            return
        message = _("Your message has been decrypted.")
        self.render(
            "messages_pop.html",
            bismuth=self.bismuth_vars,
            title=self.settings["page_title"],
            message=message,
            color="success",
            what=_("Signature"),
            data=data,
        )

    @write_protected
    async def encrypt_pop(self, params=None):
        _ = self.locale.translate
        message = self.get_argument("data", "")
        recipient = self.get_argument("recipient", "")
        self.settings["page_title"] = _("Encrypt message")
        if message == "":
            self.message_pop(_("Error:"), _("Message is empty"), "warning")
            return
        if recipient == "":
            self.message_pop(_("Error:"), _("Recipient is empty"), "warning")
            return
        try:
            data = self.bismuth.encrypt(message, recipient)
        except Exception as e:
            self.message_pop(
                _("Error:"),
                _("Could not encrypt the message.") + " " + str(e),
                "danger",
            )
            return
        message = _("Your message has been encrypted.")
        self.render(
            "messages_pop.html",
            bismuth=self.bismuth_vars,
            title=self.settings["page_title"],
            message=message,
            color="success",
            what=_("Message"),
            data=data,
        )

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "index"
        try:
            await getattr(self, command)(params)
        except Exception as e:
            self.app_log.exception("Unhandled /messages/ GET error")
            self.message_pop(
                self.locale.translate("Error:"),
                self.locale.translate("Unexpected error while processing the message request.") + " " + str(e),
                "danger",
            )

    async def post(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "sign"
        try:
            await getattr(self, command)(params, post=True)
        except Exception as e:
            self.app_log.exception("Unhandled /messages/ POST error")
            self.message_pop(
                self.locale.translate("Error:"),
                self.locale.translate("Unexpected error while processing the message request.") + " " + str(e),
                "danger",
            )


class ToolsHandler(BaseHandler):
    async def index(self, params=None, post=False):
        self.render("tools.html", bismuth=self.bismuth_vars)

    @write_protected
    async def sublimate(self, params=None):
        _ = self.locale.translate
        message = self.get_argument("data", "")
        recipient = self.get_argument("recipient", "")
        if message == "":
            self.message_pop(_("Error:"), _("Message is empty"), "warning")
            return
        if recipient == "":
            self.message_pop(_("Error:"), _("Recipient is empty"), "warning")
            return
        data = self.bismuth.encrypt(message, recipient)
        message = _("Your message has been encrypted.")
        self.render(
            "messages_pop.html",
            bismuth=self.bismuth_vars,
            title=self.settings["page_title"],
            message=message,
            color="success",
            what=_("Message"),
            data=data,
        )

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "index"
        await getattr(self, command)(params)

    async def post(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "sublimate"
        await getattr(self, command)(params, post=True)


class TxModule(tornado.web.UIModule):
    def render(self, tx):
        return self.render_string("modules/transaction.html", tx=tx)


def open_url(url):
    """Opens the default browser with our page"""
    if sys.platform == "darwin":
        # in case of OS X
        subprocess.Popen(["open", url])
    else:
        webbrowser.open_new_tab(url)


def request_shutdown():
    global SERVER_IOLOOP
    if SHUTDOWN_EVENT is not None and SERVER_IOLOOP is not None:
        SERVER_IOLOOP.add_callback(SHUTDOWN_EVENT.set)
    if MACOS_APP:
        try:
            from AppKit import NSApp
            from PyObjCTools import AppHelper
            AppHelper.callAfter(NSApp.terminate_, None)
        except Exception:
            pass


def run_server_thread():
    global SERVER_IOLOOP
    locale_path = os.path.join(helpers.base_path(), "locale")
    tornado.locale.load_gettext_translations(locale_path, "messages")
    asyncio.set_event_loop(asyncio.new_event_loop())
    SERVER_IOLOOP = tornado.ioloop.IOLoop.current()
    try:
        SERVER_IOLOOP.run_sync(main)
    finally:
        SERVER_IOLOOP = None


def run_macos_app():
    global MACOS_APP
    import objc
    from Foundation import NSObject, NSMakeRect
    from AppKit import (
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyRegular,
        NSBackingStoreBuffered,
        NSBezelStyleRounded,
        NSButton,
        NSTextField,
        NSWindow,
        NSWindowStyleMaskClosable,
        NSWindowStyleMaskMiniaturizable,
        NSWindowStyleMaskResizable,
        NSWindowStyleMaskTitled,
    )
    from PyObjCTools import AppHelper

    url = "http://127.0.0.1:{}".format(options.port)
    MACOS_APP = True
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()

    class WalletAppDelegate(NSObject):
        window = objc.ivar()

        def applicationDidFinishLaunching_(self, notification):
            frame = NSMakeRect(200.0, 200.0, 360.0, 130.0)
            style = (
                NSWindowStyleMaskTitled
                | NSWindowStyleMaskClosable
                | NSWindowStyleMaskMiniaturizable
            )
            self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame,
                style,
                NSBackingStoreBuffered,
                False,
            )
            self.window.setTitle_(options.app_title)
            self.window.center()
            self.window.setDelegate_(self)

            content = self.window.contentView()

            status = NSTextField.alloc().initWithFrame_(NSMakeRect(20.0, 72.0, 320.0, 22.0))
            status.setStringValue_("Wallet running at {}".format(url))
            status.setBezeled_(False)
            status.setDrawsBackground_(False)
            status.setEditable_(False)
            status.setSelectable_(True)
            content.addSubview_(status)

            open_button = NSButton.alloc().initWithFrame_(NSMakeRect(20.0, 22.0, 130.0, 32.0))
            open_button.setTitle_("Open Browser")
            open_button.setBezelStyle_(NSBezelStyleRounded)
            open_button.setTarget_(self)
            open_button.setAction_("openWallet:")
            content.addSubview_(open_button)

            quit_button = NSButton.alloc().initWithFrame_(NSMakeRect(165.0, 22.0, 90.0, 32.0))
            quit_button.setTitle_("Quit")
            quit_button.setBezelStyle_(NSBezelStyleRounded)
            quit_button.setTarget_(self)
            quit_button.setAction_("quitApp:")
            content.addSubview_(quit_button)

            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            # The server thread already auto-opens the wallet after binding the port.
            # Avoid a second launch here in the frozen macOS bundle.

        def openWallet_(self, sender):
            open_url(url)

        def quitApp_(self, sender):
            request_shutdown()
            NSApp.terminate_(None)

        def applicationShouldTerminate_(self, sender):
            request_shutdown()
            return True

        def windowWillClose_(self, notification):
            request_shutdown()
            NSApp.terminate_(None)

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = WalletAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
    MACOS_APP = False

    if server_thread.is_alive():
        server_thread.join(timeout=3)


async def main():
    global SHUTDOWN_EVENT
    app = Application()
    app.listen(options.port, options.listen)
    # In this demo the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    shutdown_event = tornado.locks.Event()
    SHUTDOWN_EVENT = shutdown_event
    if not options.debug:
        # In debug mode, any code change will restart the server and launch another tab.
        # This goes in the way, so we deactivate in debug.
        open_url("http://127.0.0.1:{}".format(options.port))
    await shutdown_event.wait()
    SHUTDOWN_EVENT = None


def port_in_use(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(("127.0.0.1", port))
    return result == 0


if __name__ == "__main__":
    tornado.options.parse_command_line()
    if port_in_use(options.port):
        print("Port {} is in use, opening url".format(options.port))
        if not options.romode:  # Do not auto open url in read only mode
            open_url("http://127.0.0.1:{}".format(options.port))
    elif sys.platform == "darwin" and getattr(sys, "frozen", False):
        run_macos_app()
    else:
        # See http://www.lexev.org/en/2015/tornado-internationalization-and-localization/
        run_server_thread()
