+++
title = "browserboy"
chapter = false
weight = 5
+++

![logo](/agents/browserboy/browserboy.svg?width=200px)

## Summary

browserboy is a Manifest V3 Chrome extension for Mythic. The agent uses the official `http` C2 profile. v1 uses `AESPSK=none`. Messages are `base64(UUID + JSON)`.

## Install

From the Mythic directory:

```
./mythic-cli install folder /path/to/BrowserBoy
```

Then start the container:

```
./mythic-cli start browserboy
```

## Build

1. Generate a payload in the Mythic UI.
2. Select payload type `browserboy` and C2 profile `http`.
3. Set `AESPSK` to `none`.
4. Download the ZIP.
5. Extract the ZIP.
6. Open `edge://extensions` or `chrome://extensions`.
7. Enable Developer mode.
8. Select Load unpacked.
9. Point the browser at the extracted folder.

The HTTP callback host must be reachable from the browser. The browser verifies TLS with the OS trust store. If the C2 host uses a private CA, install that CA in the OS.

## Commands

sleep, exit, identity, tabs, current, cookies, screenshot, inject, history, bookmarks, downloads, clipboard, request, load, run_loaded, redirect.

`load` accepts a JS module that exports `async function run(task, ctx)`. The module runs in a sandbox page. The sandbox has no `chrome.*` APIs. Use `ctx` for tabs, cookies, inject, and request.

## Authors

@PatchRequest
