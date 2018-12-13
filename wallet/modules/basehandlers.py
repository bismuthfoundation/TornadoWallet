

import logging
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    """Common ancestor for ann route handlers"""

    def initialize(self):
        """Common init for every request"""
        # TODO: advantage in using Tornado Babel maybe? https://media.readthedocs.org/pdf/tornado-babel/0.1/tornado-babel.pdf
        _ = self.locale.translate
        self.app_log = logging.getLogger("tornado.application")
        self.bismuth = self.settings['bismuth_client']
        # Load persisted wallet if needed
        wallet = self.get_cookie('wallet')
        if wallet and wallet != self.bismuth.wallet_file:
            self.bismuth.load_wallet(wallet)
        # print("cookies", self.cookies)
        self.bismuth_vars = self.settings['bismuth_vars']
        # self.bismuth_vars['wallet'] =
        # reflect server info
        self.settings["page_title"] = self.settings["app_title"]
        self.bismuth_vars['server'] = self.bismuth.info()
        self.bismuth_vars['server_status'] = self.bismuth.status()
        self.bismuth_vars['balance'] = self.bismuth.balance()
        self.bismuth_vars['address'] = self.bismuth_vars['server']['address']
        self.bismuth_vars['params'] = {}
        self.cristals = self.settings['bismuth_cristals']
        if self.bismuth_vars['address'] is None:
            self.bismuth_vars['address'] = _("No Bismuth address, please create or load a wallet first.")

    def active_if(self, path: str):
        """return the 'active' string if the request uri is the one in path. Used for menu css"""
        if self.request.uri == path:
            return "active"
        return ''

    def active_if_start(self, path: str):
        """return the 'active' string if the request uri begins with the one in path. Used for menu css"""
        if self.request.uri.startswith(path):
            return "active"
        return ''

    def message(self, title, message, type="info"):
        """Display message template page"""
        self.render("message.html", bismuth=self.bismuth_vars, title=title, message=message, type=type)

    def extract_params(self):
        # TODO: rewrite with get_arguments and remove this redundant function
        if '?' not in self.request.uri:
            self.bismuth_vars['params'] = {}
            return {}
        _, param = self.request.uri.split("?")
        res = {key: value for key, value in [item.split('=') for item in param.split("&")]}
        # TODO: see https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.decode_argument
        self.bismuth_vars['params'] = res
        return res


class CrystalHandler(tornado.web.RequestHandler):
    """Common ancestor for all crystals handlers"""

    """
    def __init__(self, application, request, **kwargs):
            super(tornado.web.RequestHandler, self).__init__()
    """

    def get_template_path(self):
        """Override to customize template path for each handler.

        By default, we use the ``template_path`` application setting.
        Return None to load templates relative to the calling file.
        """
        classname = self.__class__.__name__
        print(classname)
        return self.application.settings.get("template_path")
