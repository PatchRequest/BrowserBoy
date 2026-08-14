# Testing

## Unit tests

These tests do not need Chrome or Mythic.

```bash
node --test tests/protocol.test.mjs tests/timing.test.mjs
python3 -m unittest tests.test_packaging
```

`tests/protocol.test.mjs` checks UUID + JSON wrap and base64.

`tests/timing.test.mjs` checks jitter and killdate.

`tests/test_packaging.py` checks config stamp and ZIP contents.

## Playwright mock C2

```bash
npm install
npx playwright install chromium
npx playwright test
```

The test stamps an extension, starts a mock HTTP C2 server, and loads the extension in Chromium. It checks check-in and a `tabs` task.

Use `channel: "chromium"`. The Playwright headless shell does not load extensions.

## Live smoke suite

The suite tasks every command against a real Chrome instance and a live Mythic server.

Covered cases: identity, current, tabs list/create/update/reload/close, inject, cookies, history, bookmarks, downloads, clipboard write/read, request, screenshot, load, run_loaded, sleep, exit.

`exit` runs last.

```bash
python3 -m venv .venv
.venv/bin/pip install mythic
export MYTHIC_ADMIN_USER=mythic_admin
export MYTHIC_ADMIN_PASSWORD='...'
export MYTHIC_HOST=mythic
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted
```

Optional:

| Variable | Meaning |
|---|---|
| `MYTHIC_ENV_FILE` | Local `.env` with `MYTHIC_ADMIN_USER` and `MYTHIC_ADMIN_PASSWORD` |
| `MYTHIC_SSH` | SSH target. Also set `MYTHIC_ENV_REMOTE`. |
| `MYTHIC_ENV_REMOTE` | Remote path of the Mythic `.env` file |

The report is `tests/smoke/last_report.json`. That file is gitignored.
