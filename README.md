# TornadoWallet

A Python/HTML Wallet based upon the Tornado framework.

> **EXTREME WIP** Lots of work, ongoing, to be considered immature until further notice.

# Proof of concept

Not functional for now, merely a technology test.

mockup "index" and "transactions" screens only are up, with made up data.

Goal is to re-use the existing python code for behind the scene heavy lifting, but leverage HTML/JS flexibility for GUI.

# Installation

`pip3 install -r requirements.txt`

Pycryptodomex is used and may need extra install on your machine

## Mac

Install xcode compiler:

`xcode-select --install`

## Windows

WIP

# Usage

* place you wallet(s) file in wallets subdirectory
* `python3 wallet.py --theme=themes/material`
* open [http://localhost:8888](http://localhost:8888)

# Roadmap

* Proof of concept (check)
* Basic wallet functionality (check)
* Auth
* Multiwallet (partly done)
* Allinone mobile app with embedded browser and python engine

# The tech

* Tornado web app
* Templates / HTML Themes
* JS
* Embedded local webserver

# References

First HTML template derived from mBitcoin wallet.  

# Translations

Thanks to a great community effort, the wallet is available in several languages, see [translations.md](translations.md) for list and credits. 
