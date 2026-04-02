# Build TornadoWallet For Windows

This document describes the current Windows packaging workflow for TornadoWallet and the files involved in producing a Windows 11 bundle and installer.

## Current Windows packaging approach

The current Windows path is:

1. build a standalone app directory with `Nuitka`
2. package that directory into an installer with `Inno Setup`

This matches the current repo scripts:

- [make_dist_nuitka.bat](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_dist_nuitka.bat)
- [make_innosetup.iss](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_innosetup.iss)

## Why use this approach

For Windows, a standalone directory build is more practical than a single-file bundle:

- runtime resources need to sit beside the executable
- startup is generally more predictable
- packaging crypto/native dependencies is easier
- it integrates cleanly with an installer generator like Inno Setup

## Files involved

- [wallet.py](/Users/urbit/Projects/codex/TornadoWallet/wallet/wallet.py)
- [make_dist_nuitka.bat](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_dist_nuitka.bat)
- [make_innosetup.iss](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_innosetup.iss)

## Build prerequisites

Build this on a real Windows 11 machine.

Recommended prerequisites:

- Python `3.10.x`
- `pip`
- `Nuitka`
- a C compiler supported by Nuitka on Windows
- `Inno Setup`
- wallet/runtime dependencies from `requirements.txt`

The build also expects the local repo checkout of `bismuthclient` to be present, because the script points `PYTHONPATH` at the repo version:

- `..\..\BismuthClient\bismuthclient`

## Install build tools

Example commands on Windows:

```bat
py -3.10 -m pip install -r ..\requirements.txt
py -3.10 -m pip install nuitka
```

Install Inno Setup separately from its Windows installer.

## Build the standalone Windows bundle

From:

```bat
\Users\...\codex\TornadoWallet\wallet
```

run:

```bat
make_dist_nuitka.bat
```

What this script does:

- removes old `dist` and `build` directories
- copies `wallet.py` to `TornadoBismuthWallet.py`
- exposes the local repo `bismuthclient` through `PYTHONPATH`
- builds a standalone app with `Nuitka`
- copies runtime resources into `dist`

Resources currently copied into `dist`:

- `locale`
- `modules`
- `crystals`
- `crystals.available`
- `themes/material`
- `themes/common`
- `themes/mobile`
- `themes/raw`
- `news.json`
- `favicon.ico`

Expected output:

- `dist\TornadoBismuthWallet.exe`

## Build the installer

After the standalone bundle is ready, build the installer with Inno Setup using:

- [make_innosetup.iss](/Users/urbit/Projects/codex/TornadoWallet/wallet/make_innosetup.iss)

Current installer settings:

- App name: `Tornado Bismuth Wallet`
- App version: `0.1.48`
- Default install folder: `Tornado Bismuth Wallet`
- Output filename: `TornadoBismuthWallet-0.1.48-setup`

The installer currently packages everything from:

- `dist\*`

## Important notes

### Local `bismuthclient`

The Windows bundle script is designed to use the local repo version of `bismuthclient`, not just a pip-installed release.

That matters whenever local `BismuthClient` changes are required for TornadoWallet.

### Runtime resources

TornadoWallet is not just a single executable. The app expects adjacent resource directories and files.

If the app starts but pages/themes/news/crystals fail, check that the `dist` directory contains all copied resources.

### Crypto/native dependencies

The script includes current `coincurve` / `cffi` imports explicitly.

If ECDSA or ED25519-related features fail on Windows, inspect whether Nuitka bundled the required native pieces correctly.

## Current limitations

This workflow has been prepared in the repo, but it has not been executed from this macOS environment.

That means:

- the scripts are updated
- the Windows workflow is documented
- but the actual Windows executable and installer still need to be produced and tested on a Windows 11 machine

## Suggested test checklist on Windows 11

After building the app and installer, verify:

- app launches normally
- browser opens to local wallet URL
- quit behavior is acceptable
- wallet load/create works
- `/messages/` works for:
  - RSA
  - ECDSA
  - ED25519
- encryption works when recipient public key is on-chain
- home page news loads from bundled fallback and remote source
- crystals page loads without fatal startup errors
- installer creates Start Menu and desktop shortcuts correctly
- uninstall removes the installed app cleanly

## Future improvements

Potential future work for Windows packaging:

- add a dedicated Windows build note for exact compiler/toolchain setup
- decide whether to keep `Nuitka` or move to `PyInstaller` for parity
- improve installer metadata and version injection
- test code signing on Windows
- evaluate whether a small native wrapper is needed there as well
