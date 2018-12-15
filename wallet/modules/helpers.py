import sys
from os import path

import cachetools.func
import requests


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
