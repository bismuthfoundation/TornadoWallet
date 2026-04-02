#!/usr/bin/env bash
set -euo pipefail

APP_NAME="TornadoBismuthWallet"
ENTRYPOINT="wallet.py"
TEMP_ENTRYPOINT="${APP_NAME}.py"
APP_BUNDLE="dist/${APP_NAME}.app"
APP_CONTENTS="${APP_BUNDLE}/Contents"
APP_MACOS="${APP_CONTENTS}/MacOS"
DIST_DIR="dist/${APP_NAME}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

required_modules=(
  tornado
  aiohttp
  requests_oauth2
  oauthlib
  teslapy
  six
  bismuthclient
)

if [ "$(uname -s)" = "Darwin" ]; then
  required_modules+=(AppKit)
fi

missing_modules=()
for module in "${required_modules[@]}"; do
  if ! "${PYTHON_BIN}" -c "import ${module}" >/dev/null 2>&1; then
    missing_modules+=("${module}")
  fi
done

if ! "${PYTHON_BIN}" -c "import PyInstaller" >/dev/null 2>&1; then
  missing_modules+=("PyInstaller")
fi

if [ ${#missing_modules[@]} -gt 0 ]; then
  echo "Missing Python modules in build environment (${PYTHON_BIN}):"
  printf '  - %s\n' "${missing_modules[@]}"
  echo
  echo "Install them first, for example:"
  echo "  ${PYTHON_BIN} -m pip install -r ../requirements.txt pyinstaller"
  exit 1
fi

rm -rf build dist "${TEMP_ENTRYPOINT}"
cp "${ENTRYPOINT}" "${TEMP_ENTRYPOINT}"

"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name "${APP_NAME}" \
  --icon "logo.icns" \
  --hidden-import requests_oauth2 \
  --hidden-import oauthlib \
  --hidden-import tornado.locale \
  --hidden-import aiohttp \
  --hidden-import teslapy \
  --hidden-import AppKit \
  --hidden-import Foundation \
  --hidden-import objc \
  --hidden-import PyObjCTools.AppHelper \
  --hidden-import coincurve._cffi_backend \
  --hidden-import coincurve._libsecp256k1 \
  --hidden-import _cffi_backend \
  --hidden-import bismuthsimpleasset \
  --hidden-import mypolyfit \
  --hidden-import phoneapihandler \
  --hidden-import rainflow \
  --hidden-import teslaapihandler \
  --hidden-import six \
  --collect-binaries coincurve \
  "${TEMP_ENTRYPOINT}"

mkdir -p "${APP_MACOS}/themes"
mkdir -p "${DIST_DIR}/themes"
cp -R locale "${APP_MACOS}/locale"
cp -R locale "${DIST_DIR}/locale"
cp -R modules "${APP_MACOS}/modules"
cp -R modules "${DIST_DIR}/modules"
cp -R crystals "${APP_MACOS}/crystals"
cp -R crystals "${DIST_DIR}/crystals"
cp -R crystals.available "${APP_MACOS}/crystals.available"
cp -R crystals.available "${DIST_DIR}/crystals.available"
cp -R themes/material "${APP_MACOS}/themes/material"
cp -R themes/material "${DIST_DIR}/themes/material"
cp -R themes/common "${APP_MACOS}/themes/common"
cp -R themes/common "${DIST_DIR}/themes/common"
cp -R themes/mobile "${APP_MACOS}/themes/mobile"
cp -R themes/mobile "${DIST_DIR}/themes/mobile"
cp -R themes/raw "${APP_MACOS}/themes/raw"
cp -R themes/raw "${DIST_DIR}/themes/raw"
cp news.json "${APP_MACOS}/news.json"
cp news.json "${DIST_DIR}/news.json"
cp favicon.ico "${DIST_DIR}/favicon.ico"

rm -f "${TEMP_ENTRYPOINT}"

cat <<EOF
Built macOS bundle:
  ${APP_BUNDLE}

Resources were copied into:
  ${APP_MACOS}

Next steps for distribution:
  1. codesign --deep --force --options runtime --sign "Developer ID Application: <Team>" "${APP_BUNDLE}"
  2. notarize the bundle or a DMG/ZIP containing it
EOF
