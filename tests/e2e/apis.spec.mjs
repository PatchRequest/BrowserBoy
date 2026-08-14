import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { test, expect } from "@playwright/test";
import { browserChannel, launchExtension, stampExtension, waitForServiceWorker } from "./helpers.mjs";

const channel = browserChannel();

function startPageServer() {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (url.pathname === "/file.bin") {
      res.writeHead(200, {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": 'attachment; filename="probe.bin"',
      });
      res.end(Buffer.from("probe-bytes"));
      return;
    }
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Set-Cookie": "bb_probe=1; Path=/",
    });
    res.end("<!doctype html><title>BrowserBoy Probe</title><h1>probe</h1>");
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      resolve({ server, port: server.address().port });
    });
  });
}

test(`command APIs work in ${channel}`, async () => {
  const pageServer = await startPageServer();
  const work = fs.mkdtempSync(path.join(os.tmpdir(), "browserboy-api-"));
  const extDir = path.join(work, "extension");
  stampExtension(extDir, pageServer.port);

  const launched = await launchExtension(channel, extDir);
  try {
    const worker = await waitForServiceWorker(launched.context);
    const page = launched.context.pages()[0] || (await launched.context.newPage());
    const origin = `http://127.0.0.1:${pageServer.port}`;
    await page.goto(`${origin}/`, { waitUntil: "domcontentloaded" });

    const report = await worker.evaluate(async (pageOrigin) => {
      const out = {
        channelHint: (navigator.userAgentData?.brands || []).map((item) => item.brand),
        userAgent: navigator.userAgent,
        presence: {},
        results: {},
        errors: {},
      };

      const apis = {
        alarms: chrome.alarms,
        storage: chrome.storage?.local,
        tabs: chrome.tabs,
        cookies: chrome.cookies,
        scripting: chrome.scripting,
        history: chrome.history,
        bookmarks: chrome.bookmarks,
        downloads: chrome.downloads,
        identity: chrome.identity,
        offscreen: chrome.offscreen,
        getContexts: chrome.runtime?.getContexts,
      };
      for (const [name, value] of Object.entries(apis)) {
        out.presence[name] = Boolean(value);
      }

      async function record(name, workFn) {
        try {
          out.results[name] = await workFn();
        } catch (error) {
          out.errors[name] = error instanceof Error ? error.message : String(error);
        }
      }

      await record("storage", async () => {
        await chrome.storage.local.set({ bb_probe: 7 });
        const stored = await chrome.storage.local.get("bb_probe");
        return stored.bb_probe === 7;
      });

      await record("tabsQuery", async () => {
        const tabs = await chrome.tabs.query({ url: `${pageOrigin}/*` });
        return tabs.length > 0;
      });

      await record("cookies", async () => {
        const cookies = await chrome.cookies.getAll({ url: pageOrigin });
        return cookies.some((item) => item.name === "bb_probe");
      });

      await record("cookieStores", async () => {
        const stores = await chrome.cookies.getAllCookieStores();
        return Array.isArray(stores) && stores.length > 0;
      });

      await record("history", async () => {
        const items = await chrome.history.search({ text: "127.0.0.1", maxResults: 20 });
        return Array.isArray(items);
      });

      await record("bookmarks", async () => {
        const tree = await chrome.bookmarks.getTree();
        return Array.isArray(tree);
      });

      await record("downloads", async () => {
        const items = await chrome.downloads.search({});
        return Array.isArray(items);
      });

      await record("identity", async () => {
        const info = await chrome.identity.getProfileUserInfo();
        return {
          hasObject: Boolean(info) && typeof info === "object",
          email: info?.email || "",
        };
      });

      await record("platform", async () => {
        const info = await chrome.runtime.getPlatformInfo();
        return Boolean(info?.os);
      });

      await record("alarms", async () => {
        await chrome.alarms.create("bb-probe", { when: Date.now() + 60_000 });
        const alarm = await chrome.alarms.get("bb-probe");
        await chrome.alarms.clear("bb-probe");
        return Boolean(alarm);
      });

      await record("inject", async () => {
        const tabs = await chrome.tabs.query({ url: `${pageOrigin}/*` });
        if (!tabs[0]?.id) {
          throw new Error("no probe tab");
        }
        const results = await chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => document.title,
        });
        return results[0]?.result === "BrowserBoy Probe";
      });

      await record("screenshot", async () => {
        const tabs = await chrome.tabs.query({ url: `${pageOrigin}/*` });
        if (!tabs[0]?.windowId) {
          throw new Error("no probe window");
        }
        await chrome.tabs.update(tabs[0].id, { active: true });
        const dataUrl = await chrome.tabs.captureVisibleTab(tabs[0].windowId, { format: "png" });
        return typeof dataUrl === "string" && dataUrl.startsWith("data:image/png");
      });

      await record("offscreen", async () => {
        const existing = chrome.runtime.getContexts
          ? await chrome.runtime.getContexts({ contextTypes: ["OFFSCREEN_DOCUMENT"] })
          : [];
        if (!existing.length) {
          await chrome.offscreen.createDocument({
            url: "offscreen.html",
            reasons: ["CLIPBOARD", "IFRAME_SCRIPTING"],
            justification: "API probe",
          });
        }
        return true;
      });

      async function sendOffscreen(message) {
        let lastError = "no receiver";
        for (let attempt = 0; attempt < 20; attempt += 1) {
          try {
            const result = await chrome.runtime.sendMessage(message);
            if (result?.error) {
              throw new Error(result.error);
            }
            return result;
          } catch (error) {
            lastError = error instanceof Error ? error.message : String(error);
            await new Promise((resolve) => setTimeout(resolve, 100));
          }
        }
        throw new Error(lastError);
      }

      await record("clipboard", async () => {
        await sendOffscreen({
          type: "bb-clipboard",
          action: "write",
          text: "EDGE_PROBE",
        });
        const read = await sendOffscreen({ type: "bb-clipboard", action: "read" });
        return read?.output === "EDGE_PROBE";
      });

      await record("sandbox", async () => {
        const result = await sendOffscreen({
          type: "bb-sandbox-run",
          name: "probe",
          code: "export async function run(task, ctx) { return 'sandbox-ok:' + task.command; }",
          task: { id: "probe-1", command: "probe", parameters: {} },
        });
        return result?.output === "sandbox-ok:probe";
      });

      await record("sandboxCtx", async () => {
        const result = await sendOffscreen({
          type: "bb-sandbox-run",
          name: "probe-ctx",
          code: "export async function run(task, ctx) { const tabs = await ctx.tabs.query({}); return String(tabs.length); }",
          task: { id: "probe-2", command: "probe-ctx", parameters: {} },
        });
        return Number(result?.output) >= 1;
      });

      return out;
    }, origin);

    expect(report.presence, `missing APIs: ${JSON.stringify(report.presence)}`).toEqual({
      alarms: true,
      storage: true,
      tabs: true,
      cookies: true,
      scripting: true,
      history: true,
      bookmarks: true,
      downloads: true,
      identity: true,
      offscreen: true,
      getContexts: true,
    });
    expect(report.errors, `API errors: ${JSON.stringify(report.errors, null, 2)}`).toEqual({});
    expect(report.results.storage).toBe(true);
    expect(report.results.tabsQuery).toBe(true);
    expect(report.results.cookies).toBe(true);
    expect(report.results.cookieStores).toBe(true);
    expect(report.results.history).toBe(true);
    expect(report.results.bookmarks).toBe(true);
    expect(report.results.downloads).toBe(true);
    expect(report.results.identity.hasObject).toBe(true);
    expect(report.results.platform).toBe(true);
    expect(report.results.alarms).toBe(true);
    expect(report.results.inject).toBe(true);
    expect(report.results.screenshot).toBe(true);
    expect(report.results.offscreen).toBe(true);
    expect(report.results.clipboard).toBe(true);
    expect(report.results.sandbox).toBe(true);
    expect(report.results.sandboxCtx).toBe(true);
  } finally {
    await launched.context.close();
    pageServer.server.close();
    fs.rmSync(launched.tmp, { recursive: true, force: true });
    fs.rmSync(work, { recursive: true, force: true });
  }
});
