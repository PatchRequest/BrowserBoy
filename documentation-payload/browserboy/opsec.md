+++
title = "OPSEC"
chapter = false
weight = 20
+++

The extension process is Chrome. HTTP from the service worker uses the Chrome TLS stack and the browser proxy.

The manifest still lists host permissions and privileged APIs. An enterprise policy scan sees those permissions.

v1 sends `base64(UUID + JSON)` with no encryption. Use this only in a lab.

`chrome.alarms` wakes the service worker. Packed extensions have a one-minute alarm floor. Unpacked extensions allow a 30-second floor. Faster intervals use `setTimeout` only while the worker is alive.

`load` runs operator JS in a sandbox. The sandbox cannot call `chrome.*` directly.

The agent does not disable TLS verification.
