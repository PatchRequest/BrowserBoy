# OPSEC

v1 is a lab agent. Treat it as a lab agent.

## What the channel hides

The process name is Chrome. TLS looks like Chrome. Traffic uses the browser proxy.

## What the channel does not hide

- The manifest lists host permissions and privileged APIs.
- An enterprise policy scan sees those permissions.
- Sideload outside the Chrome Web Store is often blocked on managed fleets.
- Beacon interval and body size remain visible on the wire.
- v1 sends `base64(UUID + JSON)` with no encryption.
- Wire command names are Edge-style identifiers. The Mythic UI still shows `cookies` and `inject`.
- The extension still calls `chrome.cookies` and `chrome.scripting`. The manifest still lists those permissions.

## Limits

- Packed extensions have a one-minute `chrome.alarms` floor.
- Faster intervals only run while the service worker is awake.
- The agent does not disable TLS verification.
- There is no native messaging and no shell.
- There is no keylogger in v1.
- Loaded modules cannot call `chrome.*`. They use `ctx`.

## Build choices

Set `AESPSK` to `none` for v1. If you set another value, the builder fails.

Set a killdate in the HTTP profile. After that date the agent stops and clears alarms.
