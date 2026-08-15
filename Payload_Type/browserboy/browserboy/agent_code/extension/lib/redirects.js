import { compileRecord, toDnrRule } from "./redirect_rules.js";

const STORE = "edgeCompatRedirects";

async function readStore() {
  const stored = await chrome.storage.local.get(STORE);
  const box = stored[STORE] || {};
  return {
    nextId: Number.isInteger(box.nextId) && box.nextId > 0 ? box.nextId : 1,
    rules: Array.isArray(box.rules) ? box.rules : [],
  };
}

async function writeStore(box) {
  await chrome.storage.local.set({ [STORE]: box });
  return box;
}

async function applyRules(records) {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: existing.map((rule) => rule.id),
    addRules: records.map(toDnrRule),
  });
}

export async function syncRedirects() {
  const box = await readStore();
  await applyRules(box.rules);
  return box.rules;
}

export async function listRedirects() {
  const box = await readStore();
  return box.rules;
}

export async function addRedirect(args) {
  const box = await readStore();
  const record = compileRecord(box.nextId, args);
  box.nextId += 1;
  box.rules.push(record);
  await writeStore(box);
  await applyRules(box.rules);
  return record;
}

export async function removeRedirect(id) {
  const ruleId = Number(id);
  if (!Number.isInteger(ruleId) || ruleId <= 0) {
    throw new Error("redirect remove requires id");
  }
  const box = await readStore();
  const next = box.rules.filter((rule) => rule.id !== ruleId);
  if (next.length === box.rules.length) {
    throw new Error(`redirect ${ruleId} not found`);
  }
  box.rules = next;
  await writeStore(box);
  await applyRules(box.rules);
  return ruleId;
}

export async function clearRedirects() {
  const box = await readStore();
  const count = box.rules.length;
  box.rules = [];
  await writeStore(box);
  await applyRules([]);
  return count;
}
