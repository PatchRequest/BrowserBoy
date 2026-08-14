# Commands

All commands run in the service worker except `load` modules. Loaded modules run in the sandbox. See [load.md](load.md).

## sleep

Set callback interval and jitter.

```text
sleep 10 20
```

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `seconds` | number | yes | Interval in seconds |
| `jitter` | number | no | Jitter percent |

## exit

Stop alarms and mark the agent dead.

```text
exit
```

## identity

Return Chrome profile email, platform, and extension ID.

```text
identity
```

## tabs

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action` | list / create / close / update / reload | no | Default `list` |
| `tab_id` | number | for close, update, reload | Target tab |
| `url` | string | for create | Page URL |
| `active` | bool | no | Focus the tab |

```text
tabs
tabs create -url https://example.com
tabs close -tab_id 123
```

## current

Return the active tab.

```text
current
```

## cookies

No filter dumps the full jar. The agent walks every cookie store, including incognito when the user enabled the extension there.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action` | list / get / export | no | Default `list` |
| `domain` | string | no | Domain filter |
| `url` | string | for get | Cookie URL |
| `name` | string | for get | Cookie name |
| `format` | json / netscape | no | Export format |

```text
cookies
cookies -format netscape
cookies -domain example.com
```

HttpOnly cookies are included. Partitioned cookies (CHIPS) for a site without an open tab can be missing. Chrome does not give a global partitioned query.

## screenshot

Capture the visible tab. The agent uploads a PNG through Mythic file transfer.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `tab_id` | number | no | Tab to capture |
| `filename` | string | no | Name in Mythic |

## inject

Run JavaScript in a tab.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `tab_id` | number | yes | Target tab |
| `javascript` | string | yes | Source text, not base64 |
| `world` | MAIN / ISOLATED | no | Default MAIN |

```text
inject -tab_id 123 -javascript "document.title"
```

## history

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `query` | string | no | Search text |
| `max_results` | number | no | Default 100 |

## bookmarks

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action` | list / search | no | Default `list` |
| `query` | string | for search | Search text |

## downloads

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `query` | string | no | Filename or URL filter |
| `limit` | number | no | Maximum results |

## clipboard

Uses an offscreen document.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `action` | read / write | no | Default `read` |
| `text` | string | for write | Clipboard text |

The offscreen page writes to the OS clipboard when Chrome allows it. If Chrome denies the OS clipboard, the page keeps a session buffer for a later read.

## request

Send HTTP from the extension. Chrome includes cookies for hosts in `host_permissions`.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `url` | string | yes | Request URL |
| `method` | GET / POST / PUT / DELETE / PATCH / HEAD | no | Default GET |
| `headers` | JSON string | no | Header map |
| `body` | string | no | Request body |

## load

Upload a JS module and register it.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | JS identifier |
| `file` | file | yes | Module source |

## run_loaded

Run a module that `load` registered. Empty `name` lists loaded names.

| Parameter | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | no | Loaded command name |
| `args` | string | no | JSON arguments for the module |
