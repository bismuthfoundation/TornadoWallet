# Crystals

Crystals are plugins you can add to the wallet.  
They are fully contained into their own directory and only interact via the provided hooks.

Crystals can have greate power, since they can access you wallet.  
You're advised to only install trusted crystals or thoroughly check their code.

The structure and working from crystals are borrowed from the Bismuth node plugins.

## Overview

The crystals live in the "crystal" subdirectory.  
Each crystal has its own directory.  
For instance:
crystals/
crystals/100_bismuthprice/
crystals/200_dragginator/

A crystal directory has to be formated as `000_crystalname`. The numerical prefix acts as a priority level. Lowest prio gets run first.  
Priorities of 000-099 are reserved for low level crystals.  
100-199 for demo and example crystals.  
900-999 for test crystals.
In each crystal directory, at least one `__init__.py` file containing the crystal code is needed.

## Activating / Deactivating plugins

As for now, all plugins present in plugins/ directory will be loaded.  
So, only place the ones you want to run.  
You can have a "crystals.available" directory and drop unused plugins there.

> **Activate Crystals** Since crystals still are experimental, they are not activated by default.  
Run your Tornado wallet with --crystals option to activate them.

## Crystal anatomy

### Basic content injection on home

An active crystal can add panels on the wallet home page.  
This is done through the "home" filter hook.  

```
def filter_home(params):
    params["content"] += "My extra content here"
    # If you need to add extra header or footer to the home route
    params['extra']['header'] += ' <!-- dragg home extra header-->'
    params['extra']['footer'] += ' <!-- dragg home extra footer-->'
    return params
```

If you need to also inject extra css or js:  
```
def filter_home(params):
    params["content"] += "My extra content here"
    # If you need to add extra header or footer to the home route
    params['extra']['header'] += ' <!-- add home extra header-->'
    params['extra']['footer'] += ' <!-- add home extra footer-->'
    return params
```

### Content injection with sub templates

To clearly separate content from code, it's strongly advised to use sub templates.  
Check the 100_bismuthprice crystal, here is how it's architectured:

* `100_bismuthprice/themes/default/modules` contains a `home.html`subtemplate (just what we want to insert)

(WIP)

### Custom routes

WIP

## Demo crystals

WIP

See [https://github.com/bismuthfoundation/TornadoWallet/tree/master/wallet/crystals/](crystals/) directory.
