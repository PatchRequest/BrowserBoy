import { spawnSync } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect, chromium } from "@playwright/test";
import { decodeWire, encodeWire } from "../../Payload_Type/browserboy/browserboy/agent_code/extension/lib/protocol.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const CALLBACK_UUID = "11111111-2222-4333-8444-555555555555";

function startMockC2() {
  const received = [];
  const server = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      try {
        let wire = "";
        if (req.method === "GET") {
          const url = new URL(req.url, "http://127.0.0.1");
          wire = url.searchParams.get("q") || "";
        } else {
          wire = Buffer.concat(chunks).toString("utf8");
        }
        const message = decodeWire(wire);
        received.push({ method: req.method, message });
        const replyUuid = message.uuid || CALLBACK_UUID;
        let reply = { status: "success" };
        if (message.action === "checkin") {
          reply = { action: "checkin", id: CALLBACK_UUID, status: "success" };
        } else if (message.action === "get_tasking") {
          reply = {
            action: "get_tasking",
            tasks: [
              {
                id: "task-tabs-1",
                command: "tabs",
                parameters: JSON.stringify({ action: "list" }),
              },
            ],
          };
        } else if (message.action === "post_response") {
          reply = {
            action: "post_response",
            responses: (message.responses || []).map((item) => ({
              task_id: item.task_id,
              status: "success",
            })),
          };
        }
        const body = encodeWire(message.action === "checkin" ? replyUuid : CALLBACK_UUID, reply, false);
        res.writeHead(200, { "Content-Type": "text/plain" });
        res.end(body);
      } catch (error) {
        res.writeHead(500, { "Content-Type": "text/plain" });
        res.end(String(error));
      }
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({ server, port, received });
    });
  });
}

function stampExtension(dest, port) {
  const script = `
from pathlib import Path
import sys
sys.path.insert(0, ${JSON.stringify(path.join(root, "Payload_Type", "browserboy"))})
from browserboy.agent_functions.packaging import KNOWN_COMMANDS, stamp_extension
stamp_extension(
    Path(${JSON.stringify(path.join(root, "Payload_Type/browserboy/browserboy/agent_code/extension"))}),
    Path(${JSON.stringify(dest)}),
    config={
        "payload_uuid": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        "callback_host": "127.0.0.1",
        "callback_port": ${port},
        "ssl": False,
        "get_uri": "/index",
        "post_uri": "/data",
        "query_path_name": "q",
        "headers": {"User-Agent": "browserboy-test"},
        "callback_interval": 2,
        "callback_jitter": 0,
        "killdate": "2099-01-01",
        "aespsk": "none",
        "extension_name": "browserboy-test",
    },
    manifest_fields={
        "name": "browserboy-test",
        "description": "lab",
        "version": "0.0.1",
        "homepage_url": "http://127.0.0.1/",
        "update_url": "http://127.0.0.1/update.xml",
    },
    command_names=list(KNOWN_COMMANDS),
)
`;
  const result = spawnSync("python3", ["-c", script], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || "stamp failed");
  }
}

async function waitFor(predicate, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (predicate()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error("timeout waiting for mock C2 traffic");
}

test("extension checkin and tabs task use Mythic HTTP framing", async () => {
  const mock = await startMockC2();
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "browserboy-e2e-"));
  const extDir = path.join(tmp, "extension");
  const userDataDir = path.join(tmp, "chrome-profile");
  stampExtension(extDir, mock.port);

  const context = await chromium.launchPersistentContext(userDataDir, {
    channel: "chromium",
    headless: true,
    args: [
      `--disable-extensions-except=${extDir}`,
      `--load-extension=${extDir}`,
    ],
  });

  try {
    if (context.serviceWorkers().length === 0) {
      await context.waitForEvent("serviceworker", { timeout: 15000 });
    }
    await waitFor(() => mock.received.some((item) => item.message.action === "checkin"));
    const checkin = mock.received.find((item) => item.message.action === "checkin");
    expect(checkin.message.uuid).toBe("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee");
    expect(checkin.method).toBe("POST");

    await waitFor(() =>
      mock.received.some(
        (item) =>
          item.message.action === "post_response" &&
          (item.message.responses || []).some((entry) => entry.task_id === "task-tabs-1"),
      ),
    );
    const posted = mock.received.find(
      (item) =>
        item.message.action === "post_response" &&
        (item.message.responses || []).some((entry) => entry.task_id === "task-tabs-1"),
    );
    expect(posted.method).toBe("POST");
    expect(posted.message.responses[0].completed).toBe(true);
  } finally {
    await context.close();
    mock.server.close();
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
