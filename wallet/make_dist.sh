#!/usr/bin/env bash
cp wallet.py TornadoBismuthWallet.py
pyinstaller --hidden-import tornado.locale --hidden-import aiohttp --hidden-import requests_oauth2 --onefile --icon=favicon.ico TornadoBismuthWallet.py
cp -r locale dist/locale
mkdir dist/themes
cp -r themes/material dist/themes/material
cp -r themes/common dist/themes/common
cp -r crystals dist/crystals
rm TornadoBismuthWallet.py
