+++
title = "redirect"
chapter = false
weight = 17
+++

Persist `declarativeNetRequest` redirect rules.

```
redirect
redirect add google.com google2.com
redirect remove -id 1
redirect clear
```

`from` is a host, an absolute URL, or a DNR `urlFilter`. `mode` `host` keeps path and query. `mode` `url` replaces the request. `scope` `document` is navigations. `scope` `all` includes XHR and other types.

Rules survive service-worker sleep and browser restart. `exit` does not clear them.
