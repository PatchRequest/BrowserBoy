import { decodeWire, encodeWire } from "./protocol.js";

function normalizeHeaders(headers) {
  if (!headers || typeof headers !== "object") {
    return {};
  }
  return { ...headers };
}

export function buildUrl(config, kind) {
  const scheme = config.ssl ? "https" : "http";
  const port = Number(config.callback_port);
  const host = config.callback_host;
  const path = kind === "get" ? config.get_uri : config.post_uri;
  const defaultPort = scheme === "https" ? 443 : 80;
  const authority = Number.isFinite(port) && port !== defaultPort ? `${host}:${port}` : host;
  return `${scheme}://${authority}${path}`;
}

export async function sendMessage(config, uuid, payload, method) {
  const headers = normalizeHeaders(config.headers);
  if (method === "GET") {
    const url = new URL(buildUrl(config, "get"));
    url.searchParams.set(config.query_path_name || "q", encodeWire(uuid, payload, true));
    const response = await fetch(url.toString(), { method: "GET", headers, credentials: "omit" });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`GET ${response.status}`);
    }
    if (!text) {
      return {};
    }
    return decodeWire(text);
  }

  const response = await fetch(buildUrl(config, "post"), {
    method: "POST",
    headers,
    credentials: "omit",
    body: encodeWire(uuid, payload, false),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`POST ${response.status}`);
  }
  if (!text) {
    return {};
  }
  return decodeWire(text);
}

export function postMessage(config, uuid, payload) {
  return sendMessage(config, uuid, payload, "POST");
}

export function getMessage(config, uuid, payload) {
  return sendMessage(config, uuid, payload, "GET");
}
