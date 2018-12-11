# TornadoWallet

A Python/HTML Wallet based upon the Tornado framework.

> **EXTREME WIP** Lots of work, ongoing, to be considered immature until further notice.

# Proof of concept

Goal is to re-use the existing python code for behind the scene heavy lifting, but leverage HTML/JS flexibility for GUI.

First release only has minimal features

- manage wallets (unencrypted)
- auto connect to an available wallet server
- check balance and transactions
- request BIS payments
- Send simple BIS transactions
- network status

# Installation from release

See Release tab for info/installer and OS Specific FAQ.

# Installation from source

`pip3 install -r requirements.txt`

Pycryptodomex is used and may need extra install on your machine.

An auto-installer will be provided with first beta version.

## Mac

You may have to install xcode compiler:

`xcode-select --install`

then `pip3 install -r requirements.txt`

## Windows

See 
https://pycryptodome.readthedocs.io/en/latest/src/installation.html#windows-from-sources-python-3-5-and-newer

then `pip3 install -r requirements.txt`


# Usage

* `python3 wallet.py`
* open [http://localhost:8888](http://localhost:8888)

If you have no wallet yet, you'll be redirected to the wallet load page.  

Possible command line switches:    
* `--verbose --debug`
* `--theme=themes/material`  Force a specific theme
* `--server=ip:port`  Force a specific walelt server (like 127.0.0.1:8150)


## Wallet(s) location

Wallets and other potential private info are to be stored under a "bismuth-private" dir, under the user's own home directory.

The wallet prints that dir at start.  
You should also find it on the wallet/load page:  
`http://127.0.0.1:8888/wallet/load`


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
