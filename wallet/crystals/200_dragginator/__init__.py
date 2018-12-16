"""
Dragginator Crystal for Tornado wallet
"""
from os import path, listdir
import sys
import aiohttp

from modules.basehandlers import CrystalHandler
from modules.helpers import base_path
from tornado.template import Template


DEFAULT_THEME_PATH = path.join(base_path(), 'crystals/200_dragginator/themes/default')

MODULES = {}
HTTP_SESSION = None

async def async_get(url, is_json=False):
    """Async gets an url content.

    If is_json, decodes the content
    """
    global HTTP_SESSION
    # TODO: retry on error?
    if not HTTP_SESSION:
        HTTP_SESSION = aiohttp.ClientSession()
    # async with aiohttp.ClientSession() as session:
    async with HTTP_SESSION.get(url) as resp:
        if is_json:
            return await resp.json()
        else:
            return await resp.text()
        # TODO: could use resp content-type to decide


class DragginatorHandler(CrystalHandler):

    """
    def initialize(self):
        super().initialize()
        self.bismuth_vars['extra'] = {"header":'<!-- DRAGGINATOR HEADER -->', "footer": '<!-- DRAGGINATOR FOOTER -->'}
    """

    async def about(self, params=None):
        eggdrop = False
        if len(self.bismuth_vars['address']) == 56:
            data = await async_get("https://dragginator.com/api/info.php?address={}&type=list".format(self.bismuth_vars['address']),is_json=True)
            if len(data) == 0:
                eggdrop = await async_get("https://dragginator.com/api/info.php?address={}&type=eggdrop".format(self.bismuth_vars['address']),is_json=True)
        else:
            data = []
        price = await async_get("https://dragginator.com/api/info.php?type=price".format(self.bismuth_vars['address']),is_json=True)
        namespace = self.get_template_namespace()

        kwargs = {}
        namespace.update(kwargs)
        message = await async_get("https://dragginator.com/api/info.php?type=message", is_json=True)
        self.bismuth_vars['extra'] = {"header":MODULES['css'].generate(**namespace), "footer": MODULES['buy'].generate(**namespace) + MODULES['table'].generate(**namespace)}
        self.render("about.html", bismuth=self.bismuth_vars, data = data, price=price[0], eggdrop=eggdrop, message=message[0])

    async def egg(self, dna=[""]):
        _ = self.locale.translate
        data = await async_get("https://dragginator.com/api/info.php?egg={}&type=egg_info".format(dna[0]),is_json=True)
        namespace = self.get_template_namespace()
        kwargs = {"abilities": data["abilities"]}
        namespace.update(kwargs)
        self.bismuth_vars['extra'] = {"header":MODULES['css'].generate(**namespace), "footer": MODULES['egg'].generate(**namespace)+ MODULES['buy'].generate(**namespace)}

        dic = {"Fire":"danger", "Water":"info", "Earth":"success", "Air":"air",  "???":"air"}
        data["color"] = dic[data["type"]]
        dic = {"Fire":_("D:Fire egg"), "Water":_("D:Water egg"), "Earth":_("D:Earth egg"), "Air":_("D:Air egg"), "???": "???"}
        data["type"] = dic[data["type"]]
        # For registration of terms only, do not edit ever!
        void = _("D:world cup 2018"),_("D:special egg"),_("D:Cup")
        self.render("egg.html", bismuth=self.bismuth_vars, dna=dna[0], data=data)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'about'
        await getattr(self, command)(params)

    def get_template_path(self):
        """Override to customize template path for each handler."""
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
        if 'home' in MODULES:
            namespace = params['request_handler'].get_template_namespace()
            
            
            
            params["content"] += MODULES['home'].generate(**namespace)
        return params
    except Exception as e:
        print(str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
