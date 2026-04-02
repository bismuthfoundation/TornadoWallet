# How to dev

The Tornado wallet embeds a web server.

It provides routes for the selected html/js theme.  
These routes can be classic html routes like `/` or `/transactions` as well as json routes, that are prefixed by `json/`.  
These json routes can be used as a local api endpoint for any javascript need (like polling for an incoming tx).

A websocket server is also planned.


## The HTTP routes

Every route is managed by a handler that depends on the first segment of the URL.  
'/' is handled by HomeHandler and is the exception.

All other routes handlers are named after the first segment:

* /transactions/(.*)    TransactionsHandler
* /json/(.*)    JsonHandler
* /address/(.*) AddressHandler
* /messages/(.*)    AddressHandler
* /wallet/(.*)  WalletHandler
* /about/(.*)   AboutHandler
* /tokens/(.*)  TokensHandler
* /search/(.*)  SearchHandler
* /crystals/(.*)    CrystalsHandler

## Available variables

Several variables are available by default in every template, see `{{ bismuth }}` dict.

### Wallet

`{{ bismuth['address'] }}` is the Bismuth address of the currently selected wallet

### Balance

`{{ bismuth['balance'] }}` is the balance of the currently selected wallet

### Transactions

For routes `/` and `/transactions`, `{{ bismuth['transactions'] }}` is filled with a list of the most recent transactions.

### Server

### official_api

The Tornado wallet uses the official API to retrieve the current list of available and working wallet servers.  
This part is based upon the BismuthClient module.

## The Json routes

WIP - See JsonHandler in wallet.py 

## The Crystals routes and handlers

WIP

/crystals is the route for the crystalmanager.  
Every crystal is responsible for the routes of the form `/crystal/crystal_name/(.*)`

See `crystals.md`

## The websocket server

TBD
