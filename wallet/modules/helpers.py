import sys
from os import path

import cachetools.func
import requests
from bismuthclient.bismuthclient import BismuthClient

# Where the wallets and other potential private info are to be stored.
# It's a dir under the user's own home directory.
BISMUTH_PRIVATE_DIR = 'bismuth-private'


def get_private_dir():
    return BismuthClient.user_subdir(BISMUTH_PRIVATE_DIR)


def graph_colors_rgba():
    # https://flatuicolors.com/palette/defo
    return ( 'rgba(211, 84, 0,1.0)', 'rgba(39, 174, 96,1.0)', 'rgba(41, 128, 185,1.0)', 'rgba(142, 68, 173,1.0)',
           'rgba(44, 62, 80,1.0)', 'rgba(44, 62, 80,1.0)',  'rgba(243, 156, 18,1.0)', 'rgba(192, 57, 43,1.0)',
           'rgba(189, 195, 199,1.0)', 'rgba(127, 140, 141,1.0)')



def base_path():
    """Returns the full path to the current dir, whether the app is frozen or not."""
    if getattr(sys, 'frozen', False):
        # running in a bundle
        locale_path = path.dirname(sys.executable)
    else:
        # running live
        locale_path = path.abspath(path.dirname(sys.argv[0]))
    print("Local path", locale_path)
    return locale_path


@cachetools.func.ttl_cache(maxsize=5, ttl=600)
def get_api_10(url, is_json=True):
    """A Cached API getter, with 10 min cache"""
    response = requests.get(url)
    if response.status_code == 200:
        if is_json:
            return response.json()
        else:
            return response.content
    return ''
