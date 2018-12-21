pyinstaller --hidden-import tornado.locale --hidden-import aiohttp --onefile --icon=favicon.ico wallet.py
robocopy locale dist/locale /S /E *.mo
mkdir dist/themes
robocopy themes/material dist/themes/material /S /E
robocopy themes/mobile dist/themes/mobile /S /E
robocopy themes/raw dist/themes/raw /S /E
robocopy crystals dist/crystals /S /E


REM see https://nsis.sourceforge.io/Main_Page , make installer from zip
REM Or inno setup https://cyrille.rossant.net/create-a-standalone-windows-installer-for-your-python-application/
REM or https://pynsist.readthedocs.io/en/latest/index.html
