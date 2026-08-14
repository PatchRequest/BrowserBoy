const pendingCtx = new Map();
let callSeq = 0;

function callCtx(method, args) {
  const callId = `c${callSeq += 1}`;
  return new Promise((resolve, reject) => {
    pendingCtx.set(callId, { resolve, reject });
    parent.postMessage(
      {
        channel: "browserboy",
        type: "ctx",
        callId,
        method,
        args,
      },
      "*",
    );
  });
}

function makeCtx() {
  return {
    parseArgs(task) {
      if (!task.parameters) {
        return {};
      }
      if (typeof task.parameters === "object") {
        return task.parameters;
      }
      try {
        return JSON.parse(task.parameters);
      } catch {
        return { raw: task.parameters };
      }
    },
    tabs: {
      query: (queryInfo) => callCtx("tabs.query", [queryInfo]),
      get: (tabId) => callCtx("tabs.get", [tabId]),
      create: (props) => callCtx("tabs.create", [props]),
      update: (tabId, props) => callCtx("tabs.update", [tabId, props]),
      remove: (tabId) => callCtx("tabs.remove", [tabId]),
      reload: (tabId, props) => callCtx("tabs.reload", [tabId, props]),
    },
    cookies: {
      getAll: (details) => callCtx("cookies.getAll", [details]),
      get: (details) => callCtx("cookies.get", [details]),
      getAllCookieStores: () => callCtx("cookies.getAllCookieStores"),
    },
    scripting: {
      executeScript: (spec) => callCtx("scripting.executeScript", [spec]),
    },
    request: (spec) => callCtx("request", [spec]),
    identity: {
      getProfileUserInfo: () => callCtx("identity.getProfileUserInfo"),
    },
    runtime: {
      getPlatformInfo: () => callCtx("runtime.getPlatformInfo"),
    },
    history: {
      search: (query) => callCtx("history.search", [query]),
    },
    bookmarks: {
      getTree: () => callCtx("bookmarks.getTree"),
      search: (query) => callCtx("bookmarks.search", [query]),
    },
    downloads: {
      search: (query) => callCtx("downloads.search", [query]),
    },
  };
}

function rewriteModule(code) {
  if (code.includes("export async function run")) {
    return code.replace("export async function run", "async function run");
  }
  if (code.includes("export function run")) {
    return code.replace("export function run", "function run");
  }
  throw new Error("loaded file must export async function run(task, ctx)");
}

async function runModule(code, task) {
  const rewritten = rewriteModule(code);
  const run = eval(`"use strict"; ${rewritten}; run`);
  if (typeof run !== "function") {
    throw new Error("loaded module must define async function run(task, ctx)");
  }
  const output = await run(task, makeCtx());
  return output === undefined || output === null ? "" : output;
}

window.addEventListener("message", async (event) => {
  const data = event.data;
  if (!data || data.channel !== "browserboy") {
    return;
  }
  if (data.type === "ctx-result") {
    const waiter = pendingCtx.get(data.callId);
    if (!waiter) {
      return;
    }
    pendingCtx.delete(data.callId);
    if (data.error) {
      waiter.reject(new Error(data.error));
    } else {
      waiter.resolve(data.result);
    }
    return;
  }
  if (data.type !== "run") {
    return;
  }
  try {
    const output = await runModule(data.code, data.task);
    parent.postMessage(
      {
        channel: "browserboy",
        type: "done",
        requestId: data.requestId,
        output: typeof output === "string" ? output : JSON.stringify(output, null, 2),
      },
      "*",
    );
  } catch (error) {
    parent.postMessage(
      {
        channel: "browserboy",
        type: "done",
        requestId: data.requestId,
        error: error instanceof Error ? error.message : String(error),
      },
      "*",
    );
  }
});
