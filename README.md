<img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:202323,55:303635,100:e7ac80&text=LOWASS-SYNC&fontColor=f1d6b4&fontSize=58&fontAlignY=38&desc=Desktop%20apps%20%C2%B7%20UI%20Automation%20%C2%B7%20sync%20elsewhere&descSize=20&descColor=f1d6b4&descAlignY=60" width="100%" alt="" />

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-e7ac80?style=for-the-badge&logo=python&logoColor=e7ac80&labelColor=303635)](https://www.python.org/)
[![UI Automation](https://img.shields.io/badge/Windows-UI%20Automation-e7ac80?style=for-the-badge&labelColor=303635)](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview)
[![License MIT](https://img.shields.io/badge/License-MIT-e7ac80?style=for-the-badge&labelColor=303635)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/mirecekd/lowass-sync/tests.yml?branch=main&style=for-the-badge&label=TESTS&color=e7ac80&labelColor=303635)](https://github.com/mirecekd/lowass-sync/actions)

[![Buy Me a Beer](https://img.shields.io/badge/If%20you%20like%20my%20work%20you%20can-Buy%20Me%20a%20Beer-e7ac80?style=for-the-badge&labelColor=303635)](https://buymeacoffee.com/mirecekd)

</div>

## 🚀 What is LOWASS-SYNC?

A small Windows tool that reads data from desktop applications through UI Automation and syncs it elsewhere. It is a companion of [LOWASS](https://github.com/mirecekd/lowass) and shares its UI Automation probe.

**Status: early.** The UI Automation core and the probe CLI exist and the Outlook calendar tree has been inspected on Windows. There is no calendar parser, no ICS writer and no sync yet.

## 🧠 How it works?

### 1. Read
- The new Outlook (`olk.exe`, WebView2/Chromium like the new Teams) exposes its calendar to UI Automation. Every meeting is one button whose name carries the title, time, place and state.

### 2. Parse
- A pure parser (no Windows imports, tested on Linux) turns those names into meetings. The UI texts it looks for live in one table (Czech and English).

### 3. Write
- Today's meetings go to an `.ics` file, which you import into the Google Calendar of the work account (`mirdvorak@trask.cz`). A stable UID per meeting keeps a repeated import free of duplicates.

## ✨ Features

- Read-only UI Automation probe: window list, tree dump, search, live watch of changes. Nothing is clicked or typed.
- Wakes the accessibility tree of Chromium/WebView2 apps (`--enable-accessibility`).
- Planned: today's agenda parser, RFC 5545 ICS writer, `calendar_today` CLI, later the Teams calendar and other sources.

## 🛠️ Technology Stack

Python 3.11+, pywinauto (UI Automation backend, Windows only, imported lazily), pytest and ruff. Windows at runtime, tests run on Linux.

## ⚙️ Setup (Windows)

```bash
pip install -r requirements.txt
```

## 🧭 Use

Dump the Outlook window tree (calendar open, window visible and not minimised):

```bash
python -m lowass_sync.uia_probe --process olk.exe --dump --enable-accessibility --out outlook.txt
```

- `--enable-accessibility` walks the tree once and waits, which wakes the WebView2 accessibility tree.
- Other actions: `--list-windows`, `--find TEXT`, `--watch SECONDS`, `--pid N`, `--window REGEX`; defaults `--depth 40`, `--max-elements 20000`.
- Read the dump with `Get-Content outlook.txt -Encoding utf8` (the PowerShell `type` shows UTF-8 wrongly).

## 🔒 Privacy

A dump contains the visible texts, including meeting titles and names of people. Never commit it, never share it unredacted. `outlook*.txt`, `dump*.txt`, `*.ics`, `*.log` and `data/` are gitignored; tests use made-up data only.

## 🧪 Development

```bash
pip install -r requirements-dev.txt
ruff check lowass_sync tests
pytest -q
```

The probe also runs on Linux for `--help`; pywinauto is needed only on Windows.

Version format `YYYYMMDD.X` (build day and the counter of that day).

## ☕ Support

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekd) [!["PayPal.me"](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?business=LJ5ZF7Q9KMTRW&no_recurring=0&currency_code=USD)

</div>

## 📄 License

MIT License - see the `LICENSE` file for details.

## 👤 Author

Miroslav Dvorak - mirecekd@gmail.com

<img src="https://capsule-render.vercel.app/api?type=waving&height=110&section=footer&color=0:e7ac80,55:303635,100:202323" width="100%" alt="" />
