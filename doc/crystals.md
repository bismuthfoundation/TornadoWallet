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

A crystal directory has to be formatted as `000_crystalname`. The numerical prefix acts as a priority level. Lowest prio gets run first.  
Priorities of 000-099 are reserved for low level and core crystals.  
100-199 for demo and example crystals.  
900-999 for test crystals.
In each crystal directory, at least one `__init__.py` file containing the crystal code is needed.

## Activating / Deactivating plugins

As for now, all plugins present in plugins/ directory will be loaded.  
So, only place the ones you want to run.  
You can have a "crystals.available" directory and drop unused plugins there.

> **Activate Crystals** Since crystals still are experimental, they are not activated by default.  
Run your Tornado wallet with `--crystals=True` command line option to activate them.

## Crystal anatomy

### Basic content injection on home

An active crystal can add content on the wallet home page.  
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
* `def action_init(params=None):` is the init hook, called once at start. That one you can copy/paste as is, it loads (and compiles) all templates from the modules directory, and makes then available in the global MODULES dictionary.
* The `filter_home` hook is then slightly different, since we use the template:

```
def filter_home(params):
    if 'home' in MODULES:
        namespace = params['request_handler'].get_template_namespace()
        # namespace.update(kwargs)
        params["content"] += MODULES['home'].generate(**namespace)
    return params
```

- namespace gets the required defaults functions for the template to be generated  
- You can add extra variables for your custom sub template via the commented out kwargs line
- generate then produces the output to append to the content.


### Custom routes

Crystals can also have their own routes and screens.  
Route is derived from the crystal directory name.

> For instance, route for crystals/100_bismuthprice/ **will be** `/crystal/bismuthprice/(.*)`

The crystal has to implement its own handler, from CrystalHandler.  
The name of the class also is derived from the directory name.

> For instance, handler for crystals/100_bismuthprice/ **has to be** `BismuthpriceHandler` (notice the First uppercase!!!)

Ex:
```
class BismuthpriceHandler(CrystalHandler):

    async def about(self, params=None):
        self.render("about.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'about'
        await getattr(self, command)(params)

    def get_template_path(self):
        return DEFAULT_THEME_PATH 
```

`async def get` is the main - and generic - router, `async def about` matches the /crystal/bismuthprice/about route by displaying the about.html template.

Crystal specific Templates are to be placed in `themes/default` under the crystal dir.  
The convention to respect is file name = route name.  
They are supposed to extend `base.html` that is the code from the main template, and just override the `body` block, see the existing crystals.

## Demo crystals

WIP

See [https://github.com/bismuthfoundation/TornadoWallet/tree/master/wallet/crystals/](crystals/) directory.
