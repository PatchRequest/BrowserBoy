const sandbox = document.getElementById("sandbox");
const pending = new Map();

function waitForSandbox() {
  return new Promise((resolve) => {
    if (sandbox.contentWindow) {
      resolve();
      return;
    }
    sandbox.addEventListener("load", () => resolve(), { once: true });
  });
}

let sessionClipboard = "";

async function clipboardRead() {
  try {
    const text = await navigator.clipboard.readText();
    if (text !== "") {
      sessionClipboard = text;
      return text;
    }
  } catch {
    // OS clipboard can be denied in headless Chrome. Use the session buffer.
  }
  return sessionClipboard;
}

async function clipboardWrite(text) {
  sessionClipboard = text === undefined || text === null ? "" : String(text);
  try {
    await navigator.clipboard.writeText(sessionClipboard);
  } catch {
    // Session buffer still holds the value for a later read in this document.
  }
  return "ok";
}

window.addEventListener("message", async (event) => {
  const data = event.data;
  if (!data || data.channel !== "browserboy") {
    return;
  }
  if (data.type === "ctx") {
    const response = await chrome.runtime.sendMessage({
      type: "bb-ctx",
      method: data.method,
      args: data.args || [],
    });
    sandbox.contentWindow.postMessage(
      {
        channel: "browserboy",
        type: "ctx-result",
        callId: data.callId,
        result: response?.result,
        error: response?.error,
      },
      "*",
    );
    return;
  }
  if (data.type === "done") {
    const waiter = pending.get(data.requestId);
    if (!waiter) {
      return;
    }
    pending.delete(data.requestId);
    waiter(data);
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || typeof message !== "object") {
    return false;
  }
  if (message.type === "bb-clipboard") {
    const work =
      message.action === "write" ? clipboardWrite(message.text) : clipboardRead();
    work
      .then((output) => sendResponse({ output }))
      .catch((error) => sendResponse({ error: error instanceof Error ? error.message : String(error) }));
    return true;
  }
  if (message.type === "bb-sandbox-run") {
    const requestId = crypto.randomUUID();
    pending.set(requestId, (result) => {
      sendResponse({ output: result.output, error: result.error });
    });
    waitForSandbox().then(() => {
      sandbox.contentWindow.postMessage(
        {
          channel: "browserboy",
          type: "run",
          requestId,
          name: message.name,
          code: message.code,
          task: message.task,
        },
        "*",
      );
    });
    return true;
  }
  return false;
});
