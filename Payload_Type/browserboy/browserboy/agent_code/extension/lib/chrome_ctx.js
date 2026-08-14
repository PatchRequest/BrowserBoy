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

export async function dispatchChrome(method, args = []) {
  switch (method) {
    case "tabs.query":
      return promisify(chrome.tabs.query, args[0] || {});
    case "tabs.get":
      return promisify(chrome.tabs.get, args[0]);
    case "tabs.create":
      return promisify(chrome.tabs.create, args[0] || {});
    case "tabs.update":
      return promisify(chrome.tabs.update, args[0], args[1] || {});
    case "tabs.remove":
      return promisify(chrome.tabs.remove, args[0]);
    case "tabs.reload":
      return promisify(chrome.tabs.reload, args[0], args[1] || {});
    case "tabs.captureVisibleTab":
      return promisify(chrome.tabs.captureVisibleTab, args[0], args[1] || { format: "png" });
    case "cookies.getAll":
      return promisify(chrome.cookies.getAll, args[0] || {});
    case "cookies.get":
      return promisify(chrome.cookies.get, args[0]);
    case "scripting.executeScript": {
      const spec = args[0] || {};
      const world = spec.world || "MAIN";
      const results = await chrome.scripting.executeScript({
        target: { tabId: spec.tabId },
        world,
        func: (code) => eval(code),
        args: [spec.code],
      });
      return results.map((item) => item.result);
    }
    case "request": {
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
    }
    case "identity.getProfileUserInfo":
      return promisify(chrome.identity.getProfileUserInfo);
    case "runtime.getPlatformInfo":
      return promisify(chrome.runtime.getPlatformInfo);
    case "history.search":
      return promisify(chrome.history.search, args[0] || { text: "", maxResults: 100 });
    case "bookmarks.getTree":
      return promisify(chrome.bookmarks.getTree);
    case "bookmarks.search":
      return promisify(chrome.bookmarks.search, args[0] || "");
    case "downloads.search":
      return promisify(chrome.downloads.search, args[0] || {});
    default:
      throw new Error(`unknown ctx method: ${method}`);
  }
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
      query: (queryInfo) => dispatchChrome("tabs.query", [queryInfo]),
      get: (tabId) => dispatchChrome("tabs.get", [tabId]),
      create: (props) => dispatchChrome("tabs.create", [props]),
      update: (tabId, props) => dispatchChrome("tabs.update", [tabId, props]),
      remove: (tabId) => dispatchChrome("tabs.remove", [tabId]),
      reload: (tabId, props) => dispatchChrome("tabs.reload", [tabId, props]),
      captureVisibleTab: (windowId, options) =>
        dispatchChrome("tabs.captureVisibleTab", [windowId, options]),
    },
    cookies: {
      getAll: (details) => dispatchChrome("cookies.getAll", [details]),
      get: (details) => dispatchChrome("cookies.get", [details]),
    },
    scripting: {
      executeScript: (spec) => dispatchChrome("scripting.executeScript", [spec]),
    },
    request: (spec) => dispatchChrome("request", [spec]),
    identity: {
      getProfileUserInfo: () => dispatchChrome("identity.getProfileUserInfo"),
    },
    runtime: {
      getPlatformInfo: () => dispatchChrome("runtime.getPlatformInfo"),
      id: chrome.runtime.id,
    },
    history: {
      search: (query) => dispatchChrome("history.search", [query]),
    },
    bookmarks: {
      getTree: () => dispatchChrome("bookmarks.getTree"),
      search: (query) => dispatchChrome("bookmarks.search", [query]),
    },
    downloads: {
      search: (query) => dispatchChrome("downloads.search", [query]),
    },
    ...extras,
  };
}
