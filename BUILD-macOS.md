# Build TornadoWallet For macOS

This document describes the current macOS packaging workflow for TornadoWallet and the reason behind the native wrapper used in the app bundle.

## Why the macOS bundle needs a native wrapper

TornadoWallet is not a native Cocoa app. It is a local Tornado web server that opens the wallet UI in the user's browser.

A plain `PyInstaller --windowed` bundle was not enough on macOS Tahoe:

- the Dock icon kept bouncing
- the app did not behave like a fully launched macOS app
- quitting from the Dock was unreliable

### What caused the bouncing Dock icon

The bundled process was starting a local web server and opening a browser tab, but it was not providing a proper native macOS app lifecycle. From the OS point of view, the app had no real foreground window/controller to finish launch in the normal way.

### Failed approaches

1. Plain bundled server app
- Result: Dock icon kept bouncing.

2. `LSUIElement=true` agent app
- Result: bounce stopped, but the app disappeared from the Dock and there was no normal quit path.

3. `tkinter` wrapper window
- Result: this crashed on macOS Tahoe because the bundled app hit Apple's Tcl/Tk stack during startup.

### Current solution

The current macOS bundle uses a small native Cocoa wrapper via `PyObjC`.

- Tornado runs in a background thread.
- A native `NSApplication` event loop is started.
- A small Cocoa control window is shown.
- The browser is opened automatically.
- Quiting from the Dock, closing the Cocoa window, or using `/about/quit` shuts down both the native app and the Tornado server.

This is implemented in:

- [wallet.py](/Users/urbit/Projects/codex/TornadoWallet/wallet/wallet.py)

## Files involved

- [wallet.py](/Users/urbit/Projects/codex/TornadoWallet/wallet/wallet.py)
- [make_dist_mac.sh](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_dist_mac.sh)
- [make_dmg_mac.sh](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_dmg_mac.sh)

## Build prerequisites

The current build uses:

- Python `3.10.19`
- local `bismuthclient` source from the repo
- `PyInstaller`
- `PyObjC`

Install the required build packages into the build Python:

```bash
/Users/urbit/.pyenv/versions/3.10.19/bin/python -m pip install \
  pyinstaller \
  pyobjc-core \
  pyobjc-framework-Cocoa
```

Install the wallet/runtime dependencies into that same Python if needed:

```bash
cd /Users/urbit/Projects/codex/TornadoWallet
/Users/urbit/.pyenv/versions/3.10.19/bin/python -m pip install -r requirements.txt
```

Note:
- `bismuthclient` is built from the local repo checkout via `PYTHONPATH`
- do not rely on a PyPI release if local client changes are required

## Build the `.app`

From the wallet directory:

```bash
cd /Users/urbit/Projects/codex/TornadoWallet/wallet
PYTHON_BIN=/Users/urbit/.pyenv/versions/3.10.19/bin/python \
PYTHONPATH=/Users/urbit/Projects/codex/BismuthClient/bismuthclient \
PYINSTALLER_CONFIG_DIR=/Users/urbit/Projects/codex/TornadoWallet/wallet/.pyinstaller-cache \
bash make_dist_mac.sh
```

Output:

- `dist/TornadoBismuthWallet.app`

What `make_dist_mac.sh` does:

- checks that required Python modules are installed
- builds the `.app` with `PyInstaller --windowed --onedir`
- bundles the Cocoa-related imports used by the native wrapper
- copies runtime resources into the app bundle:
  - `locale`
  - `modules`
  - `crystals`
  - `crystals.available`
  - `themes`
  - `news.json`

## Optional: rename the app bundle

If you want a more user-friendly display name in `dist/`, rename the generated app before building the DMG.

Example:

```bash
mv \
  /Users/urbit/Projects/codex/TornadoWallet/wallet/dist/TornadoBismuthWallet.app \
  "/Users/urbit/Projects/codex/TornadoWallet/wallet/dist/Tornado Bismuth Wallet.app"
```

## Build the drag-to-Applications DMG

Use the DMG helper script:

```bash
APP_NAME='Tornado Bismuth Wallet' \
bash /Users/urbit/Projects/codex/TornadoWallet/wallet/make_dmg_mac.sh
```

Output:

- `dist/Tornado Bismuth Wallet.dmg`

What `make_dmg_mac.sh` does:

- creates a temporary `dmg-root` staging folder
- copies the `.app` into that folder
- adds an `Applications` symlink
- creates a writable temporary DMG
- uses Finder scripting to set:
  - icon view
  - hidden toolbar/status bar
  - tighter window size
  - centered app and `Applications` icons
- converts the temporary image into a compressed final DMG

`dmg-root` is only a temporary staging directory and can be deleted safely.

## Current expected behavior of the packaged app

On macOS, the packaged app should now:

- show a normal Dock icon
- stop bouncing after launch
- open the wallet in the browser
- show a small native control window
- quit correctly when:
  - using `Cmd+Q`
  - quitting from the Dock menu
  - closing the native window
  - opening `/about/quit` in the browser

## Troubleshooting

### Dock icon keeps bouncing

Check that the bundled app is using the Cocoa wrapper path in [wallet.py](/Users/urbit/Projects/codex/TornadoWallet/wallet/wallet.py), not an older build.

### App crashes on startup with missing Python modules

Reinstall build/runtime dependencies into the exact Python used by `PYTHON_BIN`.

### Browser quit does not close the app

Check that `request_shutdown()` in [wallet.py](/Users/urbit/Projects/codex/TornadoWallet/wallet/wallet.py) is shutting down both:

- the Tornado IOLoop
- the native Cocoa app

### DMG layout is wrong

Re-run:

```bash
APP_NAME='Tornado Bismuth Wallet' \
bash /Users/urbit/Projects/codex/TornadoWallet/wallet/make_dmg_mac.sh
```

If needed, adjust the Finder window bounds and icon positions in:

- [make_dmg_mac.sh](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_dmg_mac.sh)

## Future improvements

Potential future cleanup:

- set the Finder-visible app version in the bundle metadata instead of the current default
- make the native control window even smaller or less intrusive
- move from browser-based UI launch to an embedded webview if a more native macOS UX is desired
