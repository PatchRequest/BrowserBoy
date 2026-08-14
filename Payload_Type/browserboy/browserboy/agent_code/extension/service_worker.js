import { onAlarm, onRuntimeMessage, start } from "./lib/agent.js";

chrome.runtime.onInstalled.addListener(() => {
  start();
});
chrome.runtime.onStartup.addListener(() => {
  start();
});
chrome.alarms.onAlarm.addListener((alarm) => {
  onAlarm(alarm);
});
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const pending = onRuntimeMessage(message, sender, sendResponse);
  return pending;
});

start();
