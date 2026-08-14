import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test, expect } from "@playwright/test";
import {
  browserChannel,
  launchExtension,
  stampExtension,
  startMockC2,
  waitFor,
  waitForServiceWorker,
} from "./helpers.mjs";

const channel = browserChannel();

test(`extension checkin and tabs task use Mythic HTTP framing (${channel})`, async () => {
  const mock = await startMockC2();
  const work = fs.mkdtempSync(path.join(os.tmpdir(), "browserboy-e2e-"));
  const extDir = path.join(work, "extension");
  stampExtension(extDir, mock.port);

  const launched = await launchExtension(channel, extDir);
  try {
    await waitForServiceWorker(launched.context);
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
    await launched.context.close();
    mock.server.close();
    fs.rmSync(launched.tmp, { recursive: true, force: true });
    fs.rmSync(work, { recursive: true, force: true });
  }
});
