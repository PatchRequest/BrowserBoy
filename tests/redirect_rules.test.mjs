import test from "node:test";
import assert from "node:assert/strict";
import {
  compileRecord,
  inferMode,
  redirectAction,
  urlFilterFrom,
} from "../Payload_Type/browserboy/browserboy/agent_code/extension/lib/redirect_rules.js";

test("bare host becomes a domain urlFilter", () => {
  assert.equal(urlFilterFrom("google.com"), "||google.com^");
  assert.equal(urlFilterFrom(".google.com"), "||google.com^");
});

test("absolute URL becomes a prefix urlFilter", () => {
  assert.equal(urlFilterFrom("https://google.com/search"), "|https://google.com/search");
});

test("raw DNR filters pass through", () => {
  assert.equal(urlFilterFrom("||ads.example^"), "||ads.example^");
  assert.equal(urlFilterFrom("*://*.cdn.test/*"), "*://*.cdn.test/*");
});

test("mode host keeps the destination host", () => {
  assert.equal(inferMode("google2.com", undefined), "host");
  assert.deepEqual(redirectAction("google2.com", "host"), { transform: { host: "google2.com" } });
  assert.deepEqual(redirectAction("https://google2.com/x", "host"), {
    transform: { host: "google2.com" },
  });
});

test("mode url replaces the request", () => {
  assert.equal(inferMode("https://google2.com/", undefined), "url");
  assert.deepEqual(redirectAction("https://google2.com/", "url"), { url: "https://google2.com/" });
  assert.deepEqual(redirectAction("google2.com", "url"), { url: "https://google2.com" });
});

test("compileRecord assigns filter and action", () => {
  const record = compileRecord(3, { from: "google.com", to: "google2.com" });
  assert.equal(record.id, 3);
  assert.equal(record.mode, "host");
  assert.equal(record.urlFilter, "||google.com^");
  assert.deepEqual(record.redirect, { transform: { host: "google2.com" } });
  assert.deepEqual(record.resourceTypes, ["main_frame", "sub_frame"]);
});
