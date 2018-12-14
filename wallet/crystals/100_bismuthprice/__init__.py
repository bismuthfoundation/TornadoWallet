"""
Dragginator Crystal for Tornado wallet
"""

import requests

from os import path, listdir

import cachetools.func
from modules.basehandlers import CrystalHandler
from modules.helpers import base_path
from tornado.template import Template

DEFAULT_THEME_PATH = path.join(base_path(), 'crystals/100_bismuthprice/themes/default')

MODULES = {}

__version__ = '0.2'

class BismuthpriceHandler(CrystalHandler):

    async def about(self, params=None):
        self.render("about.html", bismuth=self.bismuth_vars, version=__version__)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'about'
        await getattr(self, command)(params)

    def get_template_path(self):
        """Override to customize template path for each handler.

        By default, we use the ``template_path`` application setting.
        Return None to load templates relative to the calling file.
        """
        return DEFAULT_THEME_PATH


@cachetools.func.ttl_cache(maxsize=5, ttl=600)
def get_api(url, is_json=True):
    """A Cached API getter"""
    # TODO: move into helpers for all to use
    print('live api request')
    response = requests.get(url)
    if response.status_code == 200:
        if is_json:
            return response.json()
        else:
            return response.content
    return ''


def action_init(params=None):
    """Load and compiles module templates"""
    modules_dir = path.join(DEFAULT_THEME_PATH, 'modules')
    for module in listdir(modules_dir):
        module_name = module.split('.')[0]
        file_name = path.join(modules_dir, module)
        with open(file_name, 'rb') as f:
            MODULES[module_name] = Template(f.read())


def filter_home(params):
    if 'home' in MODULES:
        namespace = params['request_handler'].get_template_namespace()
        api = get_api('https://bismuth.ciperyho.eu/api/markets')
        print(api)
        kwargs = {"api": api}
        namespace.update(kwargs)
        params["content"] += MODULES['home'].generate(**namespace)
        # If you need to add extra header or footer to the home route
        params['extra']['header'] += ' <!-- home extra header-->'
        params['extra']['footer'] += ' <!-- home extra footer-->'
    return params
