import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { chromium } from "@playwright/test";

const extensionDir = process.env.BROWSERBOY_EXTENSION;
if (!extensionDir) {
  throw new Error("BROWSERBOY_EXTENSION is required");
}

const holdMs = Number(process.env.BROWSERBOY_HOLD_MS || 180000);
const host = "127.0.0.1";

const SMOKE_HTML = `<!doctype html>
<html>
  <head><meta charset="utf-8"><title>BrowserBoy Smoke</title></head>
  <body>
    <h1 id="marker">browserboy-smoke-page</h1>
    <a id="dl" href="/file.bin" download="smoke.bin">download</a>
  </body>
</html>
`;

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${host}`);
  if (url.pathname === "/echo") {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("smoke-ok");
    return;
  }
  if (url.pathname === "/file.bin") {
    res.writeHead(200, {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": "attachment; filename=\"smoke.bin\"",
    });
    res.end(Buffer.from("browserboy-smoke-bytes"));
    return;
  }
  res.writeHead(200, {
    "Content-Type": "text/html; charset=utf-8",
    "Set-Cookie": "bb_smoke=1; Path=/",
  });
  res.end(SMOKE_HTML);
});

await new Promise((resolve) => server.listen(0, host, resolve));
const port = server.address().port;
const smokeUrl = `http://${host}:${port}/`;
const echoUrl = `http://${host}:${port}/echo`;
const downloadUrl = `http://${host}:${port}/file.bin`;

const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "browserboy-smoke-profile-"));
const context = await chromium.launchPersistentContext(userDataDir, {
  channel: "chromium",
  headless: true,
  args: [
    `--disable-extensions-except=${extensionDir}`,
    `--load-extension=${extensionDir}`,
  ],
});

const page = context.pages()[0] || await context.newPage();
await page.goto(smokeUrl, { waitUntil: "domcontentloaded" });
await page.evaluate(() => {
  const link = document.getElementById("dl");
  if (link) {
    link.click();
  }
});

process.stdout.write(
  `${JSON.stringify({ ready: true, smoke_url: smokeUrl, echo_url: echoUrl, download_url: downloadUrl })}\n`,
);

const stop = async () => {
  await context.close().catch(() => {});
  server.close();
  fs.rmSync(userDataDir, { recursive: true, force: true });
};

process.on("SIGTERM", () => {
  stop().finally(() => process.exit(0));
});
process.on("SIGINT", () => {
  stop().finally(() => process.exit(0));
});

await new Promise((resolve) => setTimeout(resolve, holdMs));
await stop();
