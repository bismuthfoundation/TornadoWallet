# Translations how to

TODO: Link to upper level transactions thanks you

## Mechanism
The tornado wallet uses the default mechanism provided by the Tornado Framework.  
The base `_` function is used in handlers as well as templates to mark all translatable terms, like `_("About")`

Terms and translations are stored into messages.po and messages.mo files, under their respective `locale/LNG/LC_MESSAGE` directory.

The Embedded webserver matches the closest available language from the user browser.  
Users can change language by moving a specific language at the top of their list, in their browser setting.  
This way, by default, the wallet speaks the user default language.

## Update

`make_messages.sh en` bash script is used to extract new terms from the *.py and *.html files and merge them with current messages.po file.  
One file, usually EN, is used as the reference for terms.

`compile_messages.sh en` can be used if necessary to create the .po file from the .mo one.  
It's not used in the current setup.

## Collaborative translations

We use poeditor.com online service to manage the terms, translations and contributors.

The service is free up to 1000 terms, and comes with the following features:

- Unlimited languages
- Unlimited translators
- keeps trakcs of edit history
- allows comments on terms 
- integrates (import and export) with github
- Overview of the whole process and global stats.
- Allows email notification of translators when new terms have been added. 
