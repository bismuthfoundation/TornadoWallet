#!/usr/bin/env bash
cp wallet.py TornadoBismuthWallet.py
~/.pyenv/shims/pyinstaller --hidden-import tornado.locale --hidden-import aiohttp --onefile --icon=favicon.ico TornadoBismuthWallet.py
cp -r locale dist/locale
mkdir dist/themes
cp -r themes/material dist/themes/material
cp -r crystals dist/crystals
rm TornadoBismuthWallet.py
