const HOST_RE = /^[A-Za-z0-9.-]+$/;
const ABSOLUTE_RE = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//;

const DOCUMENT_TYPES = ["main_frame", "sub_frame"];
const ALL_TYPES = [
  "main_frame",
  "sub_frame",
  "stylesheet",
  "script",
  "image",
  "font",
  "object",
  "xmlhttprequest",
  "ping",
  "csp_report",
  "media",
  "websocket",
  "other",
];

export function urlFilterFrom(from) {
  const raw = String(from || "").trim();
  if (!raw) {
    throw new Error("redirect add requires from");
  }
  if (raw.startsWith("|") || raw.includes("*")) {
    return raw;
  }
  if (ABSOLUTE_RE.test(raw)) {
    return `|${raw}`;
  }
  const host = raw.replace(/^\./, "").replace(/\/.*$/, "");
  if (!HOST_RE.test(host)) {
    throw new Error("redirect from is not a host or urlFilter");
  }
  return `||${host}^`;
}

export function inferMode(to, mode) {
  if (mode === "host" || mode === "url") {
    return mode;
  }
  if (mode) {
    throw new Error("redirect mode must be host or url");
  }
  const raw = String(to || "").trim();
  return ABSOLUTE_RE.test(raw) ? "url" : "host";
}

export function redirectAction(to, mode) {
  const raw = String(to || "").trim();
  if (!raw) {
    throw new Error("redirect add requires to");
  }
  if (mode === "host") {
    const host = ABSOLUTE_RE.test(raw)
      ? new URL(raw).hostname
      : raw.replace(/^\./, "").replace(/\/.*$/, "");
    if (!HOST_RE.test(host)) {
      throw new Error("redirect to is not a host");
    }
    return { transform: { host } };
  }
  if (ABSOLUTE_RE.test(raw)) {
    return { url: raw };
  }
  return { url: `https://${raw}` };
}

export function resourceTypesFor(scope) {
  const value = scope || "document";
  if (value === "document") {
    return DOCUMENT_TYPES.slice();
  }
  if (value === "all") {
    return ALL_TYPES.slice();
  }
  throw new Error("redirect scope must be document or all");
}

export function compileRecord(id, args) {
  const from = args.from || args.match || args.src;
  const to = args.to || args.dest || args.dst;
  const mode = inferMode(to, args.mode);
  const urlFilter = urlFilterFrom(from);
  const resourceTypes = resourceTypesFor(args.scope);
  return {
    id,
    from: String(from).trim(),
    to: String(to).trim(),
    mode,
    scope: args.scope || "document",
    urlFilter,
    resourceTypes,
    redirect: redirectAction(to, mode),
  };
}

export function toDnrRule(record) {
  return {
    id: record.id,
    priority: 1,
    action: {
      type: "redirect",
      redirect: record.redirect,
    },
    condition: {
      urlFilter: record.urlFilter,
      resourceTypes: record.resourceTypes,
    },
  };
}
