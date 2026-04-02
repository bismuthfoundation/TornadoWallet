@echo off
setlocal

set APP_NAME=TornadoBismuthWallet
set ENTRYPOINT=wallet.py
set TEMP_ENTRYPOINT=%APP_NAME%.py
set LOCAL_BISMUTHCLIENT=..\..\BismuthClient\bismuthclient

if exist dist (
  del /f /s /q dist 1>nul 2>nul
  rmdir /s /q dist
)
if exist build (
  del /f /s /q build 1>nul 2>nul
  rmdir /s /q build
)
if exist %APP_NAME%.build (
  del /f /s /q %APP_NAME%.build 1>nul 2>nul
  rmdir /s /q %APP_NAME%.build
)
if exist %APP_NAME%.dist (
  del /f /s /q %APP_NAME%.dist 1>nul 2>nul
  rmdir /s /q %APP_NAME%.dist
)
if exist %TEMP_ENTRYPOINT% del /f /q %TEMP_ENTRYPOINT%

copy %ENTRYPOINT% %TEMP_ENTRYPOINT%
if errorlevel 1 exit /b 1

set PYTHONPATH=%CD%;%LOCAL_BISMUTHCLIENT%;%PYTHONPATH%

python -m nuitka ^
  --standalone ^
  --follow-imports ^
  --show-progress ^
  --assume-yes-for-downloads ^
  --windows-icon-from-ico=favicon.ico ^
  --output-filename=%APP_NAME%.exe ^
  --include-module=requests_oauth2 ^
  --include-module=oauthlib ^
  --include-module=tornado.locale ^
  --include-module=aiohttp ^
  --include-module=teslapy ^
  --include-module=six ^
  --include-module=coincurve._cffi_backend ^
  --include-module=coincurve._libsecp256k1 ^
  --include-module=_cffi_backend ^
  %TEMP_ENTRYPOINT%
if errorlevel 1 exit /b 1

ren %APP_NAME%.dist dist
ren %APP_NAME%.build build

robocopy locale dist\locale /S /E *.mo
mkdir dist\themes 1>nul 2>nul
robocopy themes\material dist\themes\material /S /E
robocopy themes\common dist\themes\common /S /E
robocopy themes\mobile dist\themes\mobile /S /E
robocopy themes\raw dist\themes\raw /S /E
robocopy modules dist\modules /S /E
robocopy crystals dist\crystals /S /E
robocopy crystals.available dist\crystals.available /S /E
copy /Y news.json dist\news.json
copy /Y favicon.ico dist\favicon.ico

del /f /q %TEMP_ENTRYPOINT%

echo Built Windows bundle:
echo   dist\%APP_NAME%.exe
