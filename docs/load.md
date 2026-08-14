# Load

Manifest V3 forbids `eval` in the service worker. BrowserBoy runs loaded modules in a sandbox page. The sandbox allows `eval`. The sandbox has no `chrome.*` APIs.

## Module shape

```javascript
export async function run(task, ctx) {
  const tabs = await ctx.tabs.query({});
  return JSON.stringify(tabs, null, 2);
}
```

The loader removes the `export` keyword and runs `run(task, ctx)` in the sandbox.

Leviathan scripts that call `chrome.tabs` directly do not run. New modules must use `ctx`.

## ctx

| Path | Role |
|---|---|
| `ctx.parseArgs(task)` | Parse `task.parameters` as JSON |
| `ctx.tabs.query / get / create / update / remove / reload` | Tabs |
| `ctx.cookies.getAll / get` | Cookies |
| `ctx.scripting.executeScript({ tabId, code, world })` | Inject |
| `ctx.request({ url, method, headers, body })` | Authenticated fetch |
| `ctx.identity.getProfileUserInfo()` | Profile |
| `ctx.runtime.getPlatformInfo()` | Platform |
| `ctx.history.search(query)` | History |
| `ctx.bookmarks.getTree / search` | Bookmarks |
| `ctx.downloads.search(query)` | Downloads |

The service worker owns `chrome.*`. The sandbox sends RPC messages to the worker.

## Operator flow

1. Write a module that exports `run`.
2. Task `load` with `name` and the file.
3. Task `run_loaded` with that `name`.

`run_loaded` without `name` lists loaded modules.
