"""
Bismuth Voting Crystal for Tornado wallet
"""

import json
from os import path, listdir

from modules.basehandlers import CrystalHandler
from modules.helpers import base_path, get_private_dir, async_get_with_http_fallback
from tornado.template import Template
from bismuthvoting.bip39 import BIP39
from secrets import token_bytes

DEFAULT_THEME_PATH = path.join(base_path(), "crystals/020_bismuthvote/themes/default")

MODULES = {}

__version__ = "0.1"


MASTER_KEY = ""
KEYFILE = ""

# Temporarily hardcoded
# material status is the icon name assignment_late: ongoing assignment_turned_in: ended, assignment: not started yet
# {"Motion_number":"0","Motion_title":"Test motion","Motion_url":"https://hypernodes.bismuth.live/?p=863","Motion_address":"Bis1Gov1CztEShtDDddMjmzCDv9GQkuFqTzdH","Vote_start_date":1569931200,"Vote_reading_date":1571140800,"Vote_end_date":1572609600,"Options":[{"option_value":"A","option_title":"Test motion vote A"},{"option_value":"B","option_title":"Test motion vote B"}]}
# {"Motion_number":1,"Motion_title":"Reduce supply emission?","Motion_url":"https://hypernodes.bismuth.live/?p=820","Motion_address":"Bis1SUPPLYFimnbVEx9sBxLAdPWNeTyEWMVf3","Vote_start_date":1569931200,"Vote_reading_date":1572609600,"Vote_end_date":1573387200,"Options":[{"option_value":"A","option_title":"Do not change supply emission."},{"option_value":"B","option_title":"Change the supply emission to lower the dilution."}]}
BGVP_MOTIONS = []
"""
    {
        "Motion_txid": "motion_0_txid_this_would_be_a_b64_encoded_string",
        "Motion_number": "0",
        "Motion_title": "Test motion",
        "Motion_url": "https://hypernodes.bismuth.live/?p=863",
        "Motion_address": "Bis1Gov1CztEShtDDddMjmzCDv9GQkuFqTzdH",
        "Vote_start_date": 1569931200,
        "Vote_reading_date": 1571140800,
        "Vote_end_date": 1572609600,
        "Options": [
            {"option_value": "A", "option_title": "Test motion vote A"},
            {"option_value": "B", "option_title": "Test motion vote B"},
        ],
        "material_status": "assignment_late",
        "text_status": "TEST only"
    },
    {
        "Motion_txid": "MEQCIAPObnznl/wywdGtNYfIt8R2FTaBjjw2s1WMPozdwJEtAiBsoTo4",
        "Motion_number": 1,
        "Motion_title": "Reduce supply emission?",
        "Motion_url": "https://hypernodes.bismuth.live/?p=820",
        "Motion_address": "Bis1SUPPLYFimnbVEx9sBxLAdPWNeTyEWMVf3",
        "Vote_start_date": 1569931200,
        "Vote_reading_date": 1572609600,
        "Vote_end_date": 1573387200,
        "Options": [
            {"option_value": "A", "option_title": "Do not change supply emission."},
            {
                "option_value": "B",
                "option_title": "Change the supply emission to lower the dilution.",
            },
        ],
        "material_status": "assignment",
        "text_status": "Not started yet"
    },
]
"""


def status_to_gui_status(status: str) -> str:
    """Converts a motion status into material icon status"""
    if status == "Planned":
        return "assignment"
    elif status == "Voting...":
        return "assignment_late"
    elif status == "Reading...":
        return "assignment_ind"
    return "assignment_turned_in"


async def fill_motions():
    global BGVP_MOTIONS
    BGVP_MOTIONS = await async_get_with_http_fallback("https://hypernodes.bismuth.live/api/voting/motions.json")
    # print(BGVP_MOTIONS)
    for id, motion in BGVP_MOTIONS.items():
        BGVP_MOTIONS[id]["Material_status"] = status_to_gui_status(motion["Status"])


class BismuthvoteHandler(CrystalHandler):
    async def about(self, params=None):

        voting = {
            "masterkey": MASTER_KEY,
            "masterkey_file": KEYFILE,
            "key_check": BIP39.check(MASTER_KEY),
        }
        await fill_motions()
        voting["bgvp_motions"] = BGVP_MOTIONS
        self.render(
            "about.html", bismuth=self.bismuth_vars, version=__version__, voting=voting
        )

    async def motion(self, params=None):
        # TODO: message if no key is set.
        await fill_motions()
        motion_id = str(int(params[0]))  # avoid invalid inputs
        motion = BGVP_MOTIONS[motion_id]
        stats = await async_get_with_http_fallback("https://hypernodes.bismuth.live/api/voting/{}.json".format(motion_id))
        transactions = [
            {
                "signature": "random_sig",
                "timestamp": 1569932200,
                "amount": 50,
                "operation": "bgvp:vote",
                "openfield": "1:454fdkl54e==",
                "decoded": "1:C"
            }
        ]
        self.render("motion.html", bismuth=self.bismuth_vars, version=__version__, motion=motion, transactions=transactions, stats=stats)

    async def set_key(self, params=None):
        masterkey = self.get_argument("masterkey", None)
        # print("key", masterkey)
        if not masterkey:
            # Generate a new one
            entropy = token_bytes(16)
            print(entropy)
            bip39 = BIP39(entropy)
            masterkey = bip39.to_mnemonic()
        with open(KEYFILE, "w") as fp:
            fp.write(masterkey)
        global MASTER_KEY
        MASTER_KEY = masterkey
        self.redirect("/crystal/bismuthvote/")

    async def get(self, command=""):
        command, *params = command.split("/")
        if not command:
            command = "about"
        await getattr(self, command)(params)

    def get_template_path(self):
        """Override to customize template path for each handler.
        """
        return DEFAULT_THEME_PATH


def action_init(params=None):
    """Load and compiles module templates"""
    """
    modules_dir = path.join(DEFAULT_THEME_PATH, "modules")
    for module in listdir(modules_dir):
        module_name = module.split(".")[0]
        file_name = path.join(modules_dir, module)
        with open(file_name, "rb") as f:
            MODULES[module_name] = Template(f.read().decode("utf-8"))            
    """
    global MASTER_KEY
    global KEYFILE
    KEYFILE = path.join(get_private_dir(), "votingkey.json")
    if path.isfile(KEYFILE):
        with open(KEYFILE) as fp:
            MASTER_KEY = fp.readline()


def filter_home(params):
    # print("bismuthprice filter_home")
    if "home" in MODULES:
        namespace = params["request_handler"].get_template_namespace()
        """
        kwargs = {"api": api_filtered}
        namespace.update(kwargs)
        params["content"] += MODULES["home"].generate(**namespace)
        """
        # If you need to add extra header or footer to the home route
        # params['extra']['header'] += ' <!-- home extra header-->'
        # params['extra']['footer'] += ' <!-- home extra footer-->'
    return params
