const encoder = new TextEncoder();
const decoder = new TextDecoder();

export function utf8Encode(text) {
  return encoder.encode(text);
}

export function utf8Decode(bytes) {
  return decoder.decode(bytes);
}

export function concatBytes(parts) {
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

export function bytesToBase64(bytes, urlSafe = false) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  const encoded = btoa(binary);
  if (!urlSafe) {
    return encoded;
  }
  return encoded.replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

export function base64ToBytes(text) {
  const padded = text.replaceAll("-", "+").replaceAll("_", "/");
  const padLength = (4 - (padded.length % 4)) % 4;
  const normalized = padded + "=".repeat(padLength);
  const binary = atob(normalized);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    out[i] = binary.charCodeAt(i);
  }
  return out;
}

export function uuidToBytes(uuid) {
  return utf8Encode(uuid);
}
