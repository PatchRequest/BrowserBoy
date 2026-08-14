# BrowserBoy

**BrowserBoy** is a [Mythic](https://github.com/its-a-feature/Mythic) payload type. The payload is a **Manifest V3 Chrome extension**. The agent uses the official **`http`** C2 profile.

v1 is a lab build. Messages are `base64(UUID + JSON)`. Set `AESPSK` to `none`.

<p align="center">
  <img src="./agent_icons/browserboy.png" width="180" alt="BrowserBoy icon" />
</p>

Authorized red-team use only. Do not use this software without authorization.

## Install

From the Mythic install directory:

```bash
cd /path/to/Mythic
./mythic-cli install github https://github.com/PatchRequest/BrowserBoy
./mythic-cli start browserboy
```

From a local folder:

```bash
./mythic-cli install folder /path/to/BrowserBoy
./mythic-cli start browserboy
```

Use the lowercase service name `browserboy`. Docker Compose expects that name.

## Build and load

1. Open the Mythic UI.
2. Create a payload.
3. Select payload type `browserboy`.
4. Select C2 profile `http`.
5. Set `AESPSK` to `none`.
6. Download the ZIP.
7. Extract the ZIP.
8. Open `chrome://extensions`.
9. Enable Developer mode.
10. Select **Load unpacked**.
11. Point Chrome at the extracted folder.

Chrome uses the OS trust store for TLS. If the C2 host uses a private CA, install that CA on the OS.

## Commands

| Command | Role |
|---|---|
| `sleep` | Set interval and jitter |
| `exit` | Stop the agent |
| `identity` | Profile email, platform, extension ID |
| `tabs` | `list` / `create` / `close` / `update` / `reload` |
| `current` | Active tab |
| `cookies` | Full jar dump. Optional domain filter. JSON or Netscape |
| `screenshot` | Visible tab PNG |
| `inject` | Run JS in a tab |
| `history` | Search history |
| `bookmarks` | List or search |
| `downloads` | List downloads |
| `clipboard` | `read` / `write` |
| `request` | HTTP from the extension with browser cookies |
| `load` | Register a sandbox JS module |
| `run_loaded` | Run a loaded module |

See [docs/commands.md](docs/commands.md) for parameters.

## Load contract

`load` accepts a JS module that exports `async function run(task, ctx)`.

The module runs in a sandbox page. The sandbox has no `chrome.*` APIs. Use `ctx`.

See [docs/load.md](docs/load.md).

## C2

- Profile: official Mythic `http`
- Check-in and responses: POST
- Tasking: GET
- v1 crypto: `AESPSK=none`
- `encrypted_exchange_check` is not supported

See [docs/architecture.md](docs/architecture.md).

## Tests

Unit tests:

```bash
node --test tests/protocol.test.mjs tests/timing.test.mjs
python3 -m unittest tests.test_packaging
```

Playwright mock-C2 test:

```bash
npx playwright test
```

Live smoke suite (every command against Chrome + Mythic):

```bash
python3 -m venv .venv
.venv/bin/pip install mythic
export MYTHIC_ADMIN_USER=mythic_admin
export MYTHIC_ADMIN_PASSWORD=...
.venv/bin/python tests/smoke/run_live.py --extension /path/to/extracted
```

See [docs/testing.md](docs/testing.md).

## Docs

| Document | Content |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Payload type, MV3 loop, HTTP framing |
| [docs/commands.md](docs/commands.md) | Command parameters |
| [docs/load.md](docs/load.md) | Sandbox modules and `ctx` |
| [docs/testing.md](docs/testing.md) | Unit, Playwright, live smoke |
| [docs/opsec.md](docs/opsec.md) | Detection and limits |

## Layout

```text
Payload_Type/browserboy/
  Dockerfile
  main.py
  browserboy/
    agent_functions/     # Mythic commands + builder
    agent_code/extension/
tests/
  protocol.test.mjs
  timing.test.mjs
  test_packaging.py
  e2e/                   # Playwright mock C2
  smoke/                 # live command suite
docs/
```

## Related

- [Kassandra](https://github.com/PatchRequest/Kassandra) — Rust Mythic agent for Windows

## Disclaimer

Educational and authorized red-team use only. Do not use without proper authorization.

## License

BSD 3-Clause. See [LICENSE](LICENSE).
