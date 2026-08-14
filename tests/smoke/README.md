# Live smoke suite

This suite tasks every BrowserBoy command against a real Chromium or Edge instance and a live Mythic server.

## Coverage

identity, current, tabs (list/create/update/reload/close), inject, cookies, history, bookmarks, downloads, clipboard write/read, request, screenshot, load, run_loaded, sleep, exit.

`exit` runs last.

## Run

1. Build a payload in Mythic (`AESPSK=none`).
2. Extract the ZIP.
3. From the repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install mythic
export MYTHIC_ADMIN_USER=mythic_admin
export MYTHIC_ADMIN_PASSWORD='...'
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted --browser msedge
```

Default host is `mythic` on port `7443`. Default browser is Playwright `chromium`. `--browser msedge` uses Microsoft Edge.

The report is `tests/smoke/last_report.json`.
