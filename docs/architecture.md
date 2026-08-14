# Architecture

BrowserBoy is a Mythic payload type. The build output is a Manifest V3 Chrome extension ZIP.

## Pieces

| Piece | Role |
|---|---|
| `Payload_Type/browserboy` | Mythic container: builder and command classes |
| `agent_code/extension` | Service worker, commands, sandbox, offscreen page |
| Official `http` C2 profile | GET tasking, POST check-in and responses |

The builder stamps `lib/config.js`, `lib/commands.js`, and `manifest.json`. Then it minifies every `.js` file with `rjsmin` and zips the folder. Set the `minify` build parameter to off only for a readable lab payload.

## Agent loop

1. The service worker starts.
2. The agent sends a `checkin` POST.
3. Mythic returns a callback UUID.
4. The agent sends `get_tasking` on GET.
5. The agent runs each task.
6. The agent sends `post_response` on POST.
7. `setTimeout` schedules the next tick while the worker is awake.
8. `chrome.alarms` wakes the worker after idle.

Packed extensions have a one-minute alarm floor. Unpacked extensions allow a 30-second floor.

## Message format (v1)

```text
base64(UUID + JSON)
```

GET uses URL-safe base64 in the query parameter. POST uses standard base64 in the body.

Set `AESPSK` to `none`. The wrap layer is one module. AES256-HMAC can land later without a command rewrite.

## Permissions

The manifest requests:

- `alarms`, `storage`, `tabs`, `cookies`, `scripting`
- `incognito`: `spanning` so cookie stores in private windows are visible
- `history`, `bookmarks`, `downloads`
- `identity`, `identity.email`
- `clipboardRead`, `clipboardWrite`, `offscreen`
- host permission `<all_urls>`

A sandbox page runs loaded modules. An offscreen document serves clipboard and sandbox RPC.
