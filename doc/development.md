# How to dev

The Tornado wallet embeds a web server.

A websocket server is also planned.

It provides routes for the selected html/js theme.  
These routes can be classic html routes like `/` or `/transactions` as well as json routes, that are prefixed by `json/`.  
These json routes can be used as a local api endpoint for any javascript need (like polling for an incoming tx).

## The HTTP routes

## The Json routes

## The websocket server
