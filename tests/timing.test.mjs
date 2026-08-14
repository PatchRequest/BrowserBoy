import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { killdatePassed, nextDelayMs, sleepInfo } from "../Payload_Type/browserboy/browserboy/agent_code/extension/lib/timing.js";

describe("timing", () => {
  it("applies jitter in a bounded range", () => {
    const values = [];
    let i = 0;
    const sequence = [0, 0.5, 1];
    const delay = () => nextDelayMs(10, 20, () => sequence[i++ % sequence.length]);
    values.push(delay(), delay(), delay());
    assert.ok(values.every((ms) => ms >= 8000 && ms <= 12000));
    assert.ok(new Set(values).size > 1);
  });

  it("floors valid sub-second intervals at one second", () => {
    assert.equal(nextDelayMs(0.1, 0, () => 0.5), 1000);
  });

  it("treats killdate as the end of that UTC day", () => {
    assert.equal(killdatePassed("2026-01-01", new Date("2026-01-01T12:00:00Z")), false);
    assert.equal(killdatePassed("2026-01-01", new Date("2026-01-02T00:00:00Z")), true);
    assert.equal(killdatePassed("", new Date()), false);
  });

  it("formats sleep info", () => {
    assert.equal(sleepInfo(15, 10), "15s:10%");
  });
});
