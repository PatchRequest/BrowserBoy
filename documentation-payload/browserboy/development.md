+++
title = "Development"
chapter = false
weight = 15
+++

Agent sources live in `Payload_Type/browserboy/browserboy/agent_code/extension`.

The builder stamps `lib/config.js`, `lib/commands.js`, and `manifest.json`, then zips the folder.

Unit tests:

```
node --test tests/protocol.test.mjs tests/timing.test.mjs
python3 -m unittest tests.test_packaging
```

Playwright tests start a mock HTTP C2 server and load the stamped extension.
