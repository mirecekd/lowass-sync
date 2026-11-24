# lowass-sync

[![License MIT](https://img.shields.io/badge/License-MIT-e7ac80?style=for-the-badge&labelColor=303635)](LICENSE)

A small Windows tool that reads desktop-app data through UI Automation and syncs it elsewhere. Companion of
[LOWASS](https://github.com/mirecekd/lowass), sharing its UI Automation probe.

**Status: scaffold.** Only the UI Automation core and the probe CLI exist. There is no calendar parsing, no ICS writer and no sync yet.

## Planned first use case

1. Read TODAY'S MEETINGS from the new Outlook (`olk.exe`, WebView2/Chromium like the new Teams) through UI Automation.
2. Write them to an `.ics` file.
3. Import that file into the Google Calendar of the work account (`mirdvorak@trask.cz`).

Later: the Teams calendar and similar sources.

## Dump the Outlook window tree (Windows)

```bash
pip install -r requirements.txt
python -m lowass_sync.uia_probe --process olk.exe --dump --enable-accessibility --out outlook.txt
```

- The Outlook window must be visible: calendar view open, not minimised.
- `--enable-accessibility` walks the tree once and waits, which wakes the WebView2 accessibility tree.
- Other actions: `--list-windows`, `--find TEXT`, `--watch SECONDS`, `--pid N`, `--window REGEX`; defaults `--depth 40`, `--max-elements 20000`.
- Read-only: nothing is clicked or typed.

**Privacy:** a dump contains the visible texts, including meeting titles. Never commit it (`outlook*.txt` and `dump*.txt` are gitignored).

## Development

```bash
pip install -r requirements-dev.txt
ruff check lowass_sync tests
pytest -q
```

The probe also runs on Linux for `--help`; pywinauto is imported lazily and only needed on Windows.

## License

MIT, see [LICENSE](LICENSE).
