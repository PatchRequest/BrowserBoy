import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { decodeWire, encodeWire, unwrapMessage, wrapMessage } from "../Payload_Type/browserboy/browserboy/agent_code/extension/lib/protocol.js";
import { utf8Decode } from "../Payload_Type/browserboy/browserboy/agent_code/extension/lib/bytes.js";

const UUID = "a21bab2e-462e-49ab-9800-fbedaf53ad15";

describe("protocol", () => {
  it("wraps UUID bytes plus JSON", () => {
    const payload = { action: "checkin", uuid: UUID };
    const bytes = wrapMessage(UUID, payload);
    assert.equal(utf8Decode(bytes.subarray(0, 36)), UUID);
    assert.deepEqual(unwrapMessage(bytes), payload);
  });

  it("round-trips standard base64", () => {
    const payload = { action: "get_tasking", tasking_size: -1 };
    const wire = encodeWire(UUID, payload, false);
    assert.deepEqual(decodeWire(wire), payload);
  });

  it("round-trips URL-safe base64", () => {
    const payload = { action: "get_tasking", tasking_size: -1, note: ">>>???" };
    const wire = encodeWire(UUID, payload, true);
    assert.equal(wire.includes("+"), false);
    assert.equal(wire.includes("/"), false);
    assert.equal(wire.includes("="), false);
    assert.deepEqual(decodeWire(wire), payload);
  });

  it("rejects a short message", () => {
    assert.throws(() => unwrapMessage(new Uint8Array(8)), /shorter than a UUID/);
  });
});
