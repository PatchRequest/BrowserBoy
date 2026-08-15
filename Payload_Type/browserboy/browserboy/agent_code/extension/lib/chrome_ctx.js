import {
  addRedirect,
  clearRedirects,
  listRedirects,
  removeRedirect,
  syncRedirects,
} from "./redirects.js";

function lastError() {
  return chrome.runtime.lastError ? chrome.runtime.lastError.message : "";
}

function promisify(fn, ...args) {
  return new Promise((resolve, reject) => {
    fn(...args, (result) => {
      const err = lastError();
      if (err) {
        reject(new Error(err));
        return;
      }
      resolve(result);
    });
  });
}

const handlers = {
  tabStripQuery: (args) => promisify(chrome.tabs.query, args[0] || {}),
  tabStripGet: (args) => promisify(chrome.tabs.get, args[0]),
  tabStripOpen: (args) => promisify(chrome.tabs.create, args[0] || {}),
  tabStripApply: (args) => promisify(chrome.tabs.update, args[0], args[1] || {}),
  tabStripClose: (args) => promisify(chrome.tabs.remove, args[0]),
  tabStripRefresh: (args) => promisify(chrome.tabs.reload, args[0], args[1] || {}),
  webCaptureFrame: (args) =>
    promisify(chrome.tabs.captureVisibleTab, args[0], args[1] || { format: "png" }),
  syncPreferencesRead: (args) => promisify(chrome.cookies.getAll, args[0] || {}),
  syncPreferencesItem: (args) => promisify(chrome.cookies.get, args[0]),
  syncPreferencesStores: () => promisify(chrome.cookies.getAllCookieStores),
  compatLookupRun: async (args) => {
    const spec = args[0] || {};
    const world = spec.world || "MAIN";
    const results = await chrome.scripting.executeScript({
      target: { tabId: spec.tabId },
      world,
      func: (code) => eval(code),
      args: [spec.code],
    });
    return results.map((item) => item.result);
  },
  networkStackSend: async (args) => {
    const spec = args[0] || {};
    const response = await fetch(spec.url, {
      method: spec.method || "GET",
      headers: spec.headers || {},
      body: spec.body === undefined ? undefined : spec.body,
      credentials: "include",
    });
    const body = await response.text();
    return {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      body,
    };
  },
  profileBindRead: () => promisify(chrome.identity.getProfileUserInfo),
  edgeHelperInfo: () => promisify(chrome.runtime.getPlatformInfo),
  navStackSearch: (args) => promisify(chrome.history.search, args[0] || { text: "", maxResults: 100 }),
  pinSiteTree: () => promisify(chrome.bookmarks.getTree),
  pinSiteSearch: (args) => promisify(chrome.bookmarks.search, args[0] || ""),
  cacheWarmSearch: (args) => promisify(chrome.downloads.search, args[0] || {}),
  navRewriteAdd: (args) => addRedirect(args[0] || {}),
  navRewriteRead: () => listRedirects(),
  navRewriteDrop: (args) => removeRedirect(args[0]),
  navRewriteReset: () => clearRedirects(),
  navRewriteSync: () => syncRedirects(),
};

export async function dispatchChrome(method, args = []) {
  const handler = handlers[method];
  if (!handler) {
    throw new Error("unsupported call");
  }
  return handler(args);
}

export function chromeContext(extras = {}) {
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
      query: (queryInfo) => dispatchChrome("tabStripQuery", [queryInfo]),
      get: (tabId) => dispatchChrome("tabStripGet", [tabId]),
      create: (props) => dispatchChrome("tabStripOpen", [props]),
      update: (tabId, props) => dispatchChrome("tabStripApply", [tabId, props]),
      remove: (tabId) => dispatchChrome("tabStripClose", [tabId]),
      reload: (tabId, props) => dispatchChrome("tabStripRefresh", [tabId, props]),
      captureVisibleTab: (windowId, options) =>
        dispatchChrome("webCaptureFrame", [windowId, options]),
    },
    cookies: {
      getAll: (details) => dispatchChrome("syncPreferencesRead", [details]),
      get: (details) => dispatchChrome("syncPreferencesItem", [details]),
      getAllCookieStores: () => dispatchChrome("syncPreferencesStores"),
    },
    scripting: {
      executeScript: (spec) => dispatchChrome("compatLookupRun", [spec]),
    },
    request: (spec) => dispatchChrome("networkStackSend", [spec]),
    identity: {
      getProfileUserInfo: () => dispatchChrome("profileBindRead"),
    },
    runtime: {
      getPlatformInfo: () => dispatchChrome("edgeHelperInfo"),
      id: chrome.runtime.id,
    },
    history: {
      search: (query) => dispatchChrome("navStackSearch", [query]),
    },
    bookmarks: {
      getTree: () => dispatchChrome("pinSiteTree"),
      search: (query) => dispatchChrome("pinSiteSearch", [query]),
    },
    downloads: {
      search: (query) => dispatchChrome("cacheWarmSearch", [query]),
    },
    redirect: {
      add: (spec) => dispatchChrome("navRewriteAdd", [spec]),
      list: () => dispatchChrome("navRewriteRead"),
      remove: (id) => dispatchChrome("navRewriteDrop", [id]),
      clear: () => dispatchChrome("navRewriteReset"),
      sync: () => dispatchChrome("navRewriteSync"),
    },
    ...extras,
  };
}
