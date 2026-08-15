# Testing

## Unit tests

These tests do not need Chrome or Mythic.

```bash
node --test tests/protocol.test.mjs tests/timing.test.mjs
python3 -m unittest tests.test_packaging tests.test_aliases tests.test_smoke_browser
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

The tests stamp an extension and load it with `--load-extension`.

- `extension.spec.mjs` starts a mock HTTP C2 server. It checks check-in and a `tabs` task.
- `apis.spec.mjs` calls every `chrome.*` API that the commands use. It also runs clipboard, sandbox `eval`, and sandbox `ctx` RPC.

Use a full browser channel. The Playwright headless shell does not load extensions.

```bash
npx playwright test
BROWSERBOY_CHANNEL=msedge npx playwright test
```

`msedge` needs Microsoft Edge on the machine:

```bash
npx playwright install msedge
```

Verified on Microsoft Edge 151 (this repo, headless `--load-extension`):

| Surface | Result |
|---|---|
| Check-in and `tabs` over mock HTTP | pass |
| `storage`, `tabs`, `cookies` (all stores), `history`, `bookmarks`, `downloads` | pass |
| `scripting.executeScript`, `captureVisibleTab` | pass |
| `alarms`, `offscreen`, clipboard session buffer | pass |
| Sandbox `eval` and sandbox `ctx` RPC (`load` / `run_loaded` path) | pass |
| `identity.getProfileUserInfo` | API present. Email is often empty. |

Live Mythic smoke on Edge uses `--browser msedge`. That run is separate from the Playwright suite.

## Live smoke suite

The suite tasks every command against a real Chromium or Edge instance and a live Mythic server.

Covered cases: identity, current, tabs list/create/update/reload/close, inject, cookies, history, bookmarks, downloads, clipboard write/read, request, screenshot, load, run_loaded, sleep, exit.

`exit` runs last.

```bash
python3 -m venv .venv
.venv/bin/pip install mythic
export MYTHIC_ADMIN_USER=mythic_admin
export MYTHIC_ADMIN_PASSWORD='...'
export MYTHIC_HOST=mythic
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted --browser msedge
```

Optional:

| Variable | Meaning |
|---|---|
| `MYTHIC_ENV_FILE` | Local `.env` with `MYTHIC_ADMIN_USER` and `MYTHIC_ADMIN_PASSWORD` |
| `MYTHIC_SSH` | SSH target. Also set `MYTHIC_ENV_REMOTE`. |
| `MYTHIC_ENV_REMOTE` | Remote path of the Mythic `.env` file |

The report is `tests/smoke/last_report.json`. That file is gitignored.
