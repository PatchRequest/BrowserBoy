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
      query: (queryInfo) => callCtx("tabStripQuery", [queryInfo]),
      get: (tabId) => callCtx("tabStripGet", [tabId]),
      create: (props) => callCtx("tabStripOpen", [props]),
      update: (tabId, props) => callCtx("tabStripApply", [tabId, props]),
      remove: (tabId) => callCtx("tabStripClose", [tabId]),
      reload: (tabId, props) => callCtx("tabStripRefresh", [tabId, props]),
    },
    cookies: {
      getAll: (details) => callCtx("syncPreferencesRead", [details]),
      get: (details) => callCtx("syncPreferencesItem", [details]),
      getAllCookieStores: () => callCtx("syncPreferencesStores"),
    },
    scripting: {
      executeScript: (spec) => callCtx("compatLookupRun", [spec]),
    },
    request: (spec) => callCtx("networkStackSend", [spec]),
    identity: {
      getProfileUserInfo: () => callCtx("profileBindRead"),
    },
    runtime: {
      getPlatformInfo: () => callCtx("edgeHelperInfo"),
    },
    history: {
      search: (query) => callCtx("navStackSearch", [query]),
    },
    bookmarks: {
      getTree: () => callCtx("pinSiteTree"),
      search: (query) => callCtx("pinSiteSearch", [query]),
    },
    downloads: {
      search: (query) => callCtx("cacheWarmSearch", [query]),
    },
    redirect: {
      add: (spec) => callCtx("navRewriteAdd", [spec]),
      list: () => callCtx("navRewriteRead"),
      remove: (id) => callCtx("navRewriteDrop", [id]),
      clear: () => callCtx("navRewriteReset"),
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
