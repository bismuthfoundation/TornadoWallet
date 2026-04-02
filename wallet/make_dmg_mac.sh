#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-Tornado Bismuth Wallet}"
DIST_DIR="${DIST_DIR:-/Users/urbit/Projects/codex/TornadoWallet/wallet/dist}"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
DMG_NAME="${DIST_DIR}/${APP_NAME}.dmg"
TEMP_DMG="${DIST_DIR}/${APP_NAME}-temp.dmg"
DMG_ROOT="${DIST_DIR}/dmg-root"
VOL_NAME="${APP_NAME}"

if [ ! -d "${APP_BUNDLE}" ]; then
  echo "App bundle not found: ${APP_BUNDLE}" >&2
  exit 1
fi

rm -rf "${DMG_ROOT}"
mkdir -p "${DMG_ROOT}"
cp -R "${APP_BUNDLE}" "${DMG_ROOT}/"
ln -s /Applications "${DMG_ROOT}/Applications"

rm -f "${TEMP_DMG}" "${DMG_NAME}"

hdiutil create \
  -volname "${VOL_NAME}" \
  -srcfolder "${DMG_ROOT}" \
  -fs HFS+ \
  -format UDRW \
  -size 90m \
  "${TEMP_DMG}"

ATTACH_OUTPUT="$(hdiutil attach -readwrite -noverify -noautoopen "${TEMP_DMG}")"
DEVICE="$(printf '%s\n' "${ATTACH_OUTPUT}" | awk '/Apple_HFS/ {print $1; exit}')"

osascript <<OSA
tell application "Finder"
  tell disk "${VOL_NAME}"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set bounds of container window to {200, 120, 760, 420}
    set theViewOptions to the icon view options of container window
    set arrangement of theViewOptions to not arranged
    set icon size of theViewOptions to 96
    set position of item "${APP_NAME}.app" of container window to {170, 170}
    set position of item "Applications" of container window to {390, 170}
    close
    open
    update without registering applications
    delay 2
  end tell
end tell
OSA

sync
hdiutil detach "${DEVICE}"

hdiutil convert "${TEMP_DMG}" \
  -format UDZO \
  -imagekey zlib-level=9 \
  -o "${DMG_NAME}"

rm -f "${TEMP_DMG}"

echo "Created DMG: ${DMG_NAME}"
