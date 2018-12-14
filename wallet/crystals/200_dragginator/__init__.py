"""
Dragginator Crystal for Tornado wallet
"""
from os import path, listdir
import sys

from modules.basehandlers import CrystalHandler
from modules.helpers import base_path
from tornado.template import Template

DEFAULT_THEME_PATH = path.join(base_path(), 'crystals/200_dragginator/themes/default')

MODULES = {}

class DragginatorHandler(CrystalHandler):

    def initialize(self):
        super().initialize()
        self.bismuth_vars['extra'] = {"header":'<!-- DRAGGINATOR HEADER -->', "footer": '<!-- DRAGGINATOR FOOTER -->'}

    async def about(self, params=None):
        self.render("about.html", bismuth=self.bismuth_vars)

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
        print("DragginatorHandler get_template_path")
        return DEFAULT_THEME_PATH


def action_init(params=None):
    """Load and compiles module templates"""
    modules_dir = path.join(DEFAULT_THEME_PATH, 'modules')
    for module in listdir(modules_dir):
        module_name = module.split('.')[0]
        file_name = path.join(modules_dir, module)
        with open(file_name, 'rb') as f:
            MODULES[module_name] = Template(f.read())


def filter_home(params):
    try:
        # params["content"] += b"Dragginator"
        if 'home' in MODULES:
            namespace = params['request_handler'].get_template_namespace()
            # namespace.update(kwargs)
            params["content"] += MODULES['home'].generate(**namespace)
            # If you need to add extra header or footer to the home route
            params['extra']['header'] += ' <!-- dragg home extra header-->'
            params['extra']['footer'] += ' <!-- dragg home extra footer-->'

        return params
    except Exception as e:
        print(str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
