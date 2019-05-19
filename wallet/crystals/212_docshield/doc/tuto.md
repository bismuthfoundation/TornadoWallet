# Docshield Tutorial: From need, to idea, to wallet embedded dApp.

In this tutorial I'll guide you behind the scenes in the making of the DocShield Crystal dApp.  
The Docshield itself is a nice use case for the Bismuth blockchain, but the ease of development of such an application on top of Bismuth’s infrastructure demonstrates better than anything why BIS is a platform of choice for dApp developers-  no matter their experience or familiarity with Python.  

## The beginning

One of our Crystal developers had a precise need for Intellectual property protection, exposed in the https://hypernodes.bismuth.live/?p=494 post.  
That could be done with on-chain registration/query of data, and he gave a try to build a simple but effective dApp with the Crystal framework.

## Tornado Wallet
The Tornado wallet (https://github.com/bismuthfoundation/TornadoWallet) is a regular GUI wallet, a powerful framework, and API server.  
It embeds:
- A low level connection layer to the Bismuth wallet server infrastructure (no obligation to run a local node)  
- Python framework with many helpers and plugin support  
- A Web server  
- A them-able HTML wallet, running on top of the framework  
- A JSON API server for any wallet server supported command  
- A JS framework  

## Crystals 
Crystals can be seen as plugins. They are additional code that adds features to the wallet, and allows to seamlessly interact with dApps.  
The framework is powerful, and allows to code the same thing via different approaches.

# The Approach

This Crystal will focus on the JS framework. We'll suppose you have minimal Python experience, and handle most of the code as vanilla Javascript and jQuery.  
Crystal development is easy for anyone with basic web development knowledge- no need to be a blockchain or python guru.

## Only 3 "code" files

Have a look at the crystal repo: all code for the whole dApp is there.  
about.json is basic metadata: Description, author, version and such.

The 3 important files are 
- `__init__.py` , the python handler
- `about.html`, the html template
- `docshield.js` , the main js code

> We'll now get into more details about the scaffold, but in the end, all that you'll really need to know is call the `send(address, amount, operation, datafield);` javascript function, and query chain data via simple http json endpoint.  
The rest is just plumbing and html/css design.  


### The python side

This is almost the minimal code required to run a crystal.  
Here it is in full:
```python
from os import path, listdir

from modules.basehandlers import CrystalHandler
from modules.i18n import get_dt_language
from modules.helpers import base_path


DEFAULT_THEME_PATH = path.join(base_path(), 'crystals/212_docshield/themes/default')

MODULES = {}

__version__ = '1.0'


class DocshieldHandler(CrystalHandler):

    def initialize(self):
        # Parent init
        super().initialize()
        # Inject our local js file in the template footer, so js code is seen after jquery
        with open('crystals/212_docshield/themes/default/docshield.js', 'r') as file:
            data = file.read()
        self.bismuth_vars['extra'] = {"header":'<!-- DOCHASH HEADER -->', "footer": data}

    async def about(self, params=None):
        namespace = self.get_template_namespace()
        self.bismuth_vars['dtlanguage'] = get_dt_language(self.locale.translate)
        kwargs = {"bismuth": self.bismuth_vars}
        namespace.update(kwargs)
        self.render("about.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'about'
        await getattr(self, command)(params)

    def get_template_path(self):
        """Override to customize template path for each handler."""
        return DEFAULT_THEME_PATH

    def static(self):
        """Defining this method will automagically create a static handler pointing to local /static crystal dir"""
        pass
```

Refer to https://github.com/bismuthfoundation/TornadoWallet/blob/master/doc/crystals.md for a more complete reference of crystals.

The important parts are:  
- `class DocshieldHandler(CrystalHandler):` : defines the class for the crystal handler, see doc above for naming convention.
- `async def about(self, params=None):` It's the handler for the only view needed by the app, with /about/ route.  
It takes care of handling the i18n variables, then renders the about.html template. **This is generic code**.
- `def initialize(self):` Since we need custom JS, and prefer to isolate template from code, the JS lies in a separate file, that we inject in the footer of the html page.  
We open the js file, and inject its content in footer via the "extra" bismuth var. Again, except for the path, **this is generic code you can copy/paste for your own crystal**.
- `def static(self)` We wanted to embed a picture as local file. Defining this function, no need for any code in it, just "pass", and the framework will add a /crystal/dochash/static/ route, with a full featured static file handler behind the scenes. **Also generic**.

> So Here, apart from the naming convention, everything is generic code you can use as is to bootstrap your own crystal.


### The HTML Template

 The Wallet framework uses Tornado Templates. See ref here : https://www.tornadoweb.org/en/stable/template.html
 
 Variables are like `{{ var_name }}` and you can use python alike syntax for loops and conditions.
 
 See the full html template source code: (LINK)  
 The wallet is themeable, so what we're dealing with is only the content part of the GUI. Menu, sidebar, footer, are handled by the global theme.
 
 The core of our template is like 
 ```
{% extends "base.html" %}
{% block body %}
OUR VIEW CONTENT HERE
{% end %}
```

The base theme uses the bootstrap css framework, should not be new for any web dev.

The content itself is 4 blocks:

(SCREEN)

- 1: Logo
- 2: Document loading form and info
- 3: Transactions submission form
- 4: Datatables for already registered docs.

No code in there, you'll just find a few "onclick" events to trigger the required actions, all is GUI and HTML bootstrap.

### The Javascript

Here comes the real code, that interacts with the chain.  
Don't be afraid, there's only a few lines of code there.

Full code: (LINK)

As you can see, a few additional libraries were added.
With time, most commonly used libraries will be integrated as part of the framework/main theme. 

#### Load the document, hash it. 

```javascript
function loadFile(address) {
    if(address.length == 56) {
        input = document.getElementById('ip-file-input');
        file = input.files[0];
        $('#ip-file-size').val(file.size.toString());
        $('#ip-file-name').val(file.name);

        var reader = new FileReader();
        reader.onloadend = function(evt) {
            if (evt.target.readyState == FileReader.DONE) { // DONE == 2
                var hexdigest = CryptoJS.SHA256(CryptoJS.enc.Latin1.parse(evt.target.result)).toString(CryptoJS.enc.Hex)
                $('#ip-file-hash').val(hexdigest);

                $('#ip-recipient').val(address);
                // Transaction 1
                $('#ip-operation-1').val('dochash:sha256');
                datafield1 = hexdigest;
                $('#ip-datafield-1').val(datafield1);
                $('#ip-fee-1').html(0.01 + 1e-5*datafield1.length);
                // Transaction 2
                $('#ip-operation-2').val('dochash:json');
                datafield2 = '{"filename":"' + file.name + '", "size":' + file.size + ', "hash_type":"sha256", "hash":"' + hexdigest + '"}';
                $('#ip-datafield-2').val(datafield2);
                $('#ip-fee-2').html(0.01 + 1e-5*datafield2.length);

                check_exactopdata('dochash:sha256',datafield1,$('#ip-file-ledger-1'));
                check_exactopdata('dochash:json',datafield2,$('#ip-file-ledger-2'));

                update_table(address);
            }
        }
        var blob = file.slice(0, file.size);
        reader.readAsBinaryString(blob);
    } else {
        alert("First select a wallet address.");
    }
}
```

No magic in there. CryptoJS.SHA256 does the hash job, browser side, then we fill in required values.

#### Emit the transactions

```javascript
function ipSubmit(tx,balance) {
    address = $('#ip-recipient').val();

    if(tx == 1) {
        fee = parseFloat($('#ip-fee-1').val());
        operation = $('#ip-operation-1').val();
        datafield = $('#ip-datafield-1').val();
    } else {
        fee = parseFloat($('#ip-fee-2').val());
        operation = $('#ip-operation-2').val();
        datafield = $('#ip-datafield-2').val();
    }

    if(address.length == 56) {
        if(balance>=fee) {
            status = check_exactopdata(operation,datafield,'');
            if(status == "No") {
                send(address, 0, operation, datafield);
            } else {
                alert('Data already exists in ledger.');
            }
        } else {
            alert("Insufficient account balance.");
        }
    } else {
        alert("Not a valid recipient address.");
    }
} 
```

Each transaction is composed of an amount (0 here), an operation code (dochash:sha256 or dochash:json) as well as a data payload.  
This function gathers all that data, checks that this file is not registered already (we'll see later on) and "sends" the transaction, 
via the most simple `send(address, amount, operation, datafield);` javascript call.  
*This may be all you need to write your crystal: use that "send" call on purpose*.

In fact, this "send" call does not send the transaction straight away, but trigger the framework to ask confirmation to the user.  
So the user will see the confirm pop up show, and will be required to confirm the operation. A plugin can not emit transaction or sign without a user confirmation.  
Moreover, with the integrated "spend protection", the user can configure an additional safety, like a PIN code to enter.


#### Check a document already is registered

Just above, we used check_exactopdata to check wether a specific document (hash) was already registered.  
This means querying the chain for the same exact match operation and data fields (whatever the address is).

Again, this is ridiculously easy, because the wallet acts as a Json API endpoint. 
It allows to use direct wallet server commands as pure http requests.  
Newest wallet servers know the `listexactopdatajson`command, so we just have to query that:    

```javascript
function check_exactopdata(op, data, field) {
    // Lookup for an exact match on operation and data fields.
    // Uses the integrated json gateway from the tornado wallet.
    url = 'http://127.0.0.1:8888/json/listexactopdatajson/' + op + '/' + data;
    response = JSON.parse(httpGet(url));
    if(response.length>0) {
        status = 'Yes';
    } else {
        status = 'No';
    }
    if(field) {
        field.val(status);
    }
    return status;
} 
```

`httpGet(url)` is a js function defined by the framework, you can use it also.

See the wallet server supported commands : (LINK)

#### Build the datatable content

Last step, fill the datatable with all the docs we already registered.  
Again, we make use of the Json api "addlist" , that we then filter out.

```javascript
function update_table(address) {
    // Ledger query
    url = 'http://127.0.0.1:8888/json/addlist/' + address;
    // TODO: maybe a stricter query could be use, to avoid huge data on busy addresses
    // Like get exact address + partial dochash:%
    response = JSON.parse(httpGet(url));
    table.clear();
    for(i=0; i<response.length-1; i++) {
        if (response[i][10].startsWith('dochash:')) {
            table.row.add([response[i][0], ts_to_ymdhms(response[i][1]),response[i][10],response[i][11]]).draw();
        }
    }
}
```

# In the end

This tutorial was quite lenghty as we tried to cover everything. 
Give it a try with a Crystal of your own, cloning an existing crystal as a basis, and you'll see that it takes very little effort to interact with the chain.

Also, note that if you are more comfortable with Python than Javascript, all that was done here on the browser side could have been done also directly in the python handlers. It's your choice. 

