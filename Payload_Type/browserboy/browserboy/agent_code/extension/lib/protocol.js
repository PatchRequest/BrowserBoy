import { base64ToBytes, bytesToBase64, concatBytes, utf8Decode, utf8Encode, uuidToBytes } from "./bytes.js";

const UUID_LENGTH = 36;

export function wrapMessage(uuid, payload) {
  const body = utf8Encode(JSON.stringify(payload));
  return concatBytes([uuidToBytes(uuid), body]);
}

export function unwrapMessage(bytes) {
  if (bytes.length < UUID_LENGTH) {
    throw new Error("agent message is shorter than a UUID");
  }
  const json = utf8Decode(bytes.subarray(UUID_LENGTH));
  if (!json) {
    return {};
  }
  return JSON.parse(json);
}

export function encodeWire(uuid, payload, urlSafe = false) {
  return bytesToBase64(wrapMessage(uuid, payload), urlSafe);
}

export function decodeWire(text) {
  return unwrapMessage(base64ToBytes(text.trim()));
}
