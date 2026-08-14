async function hasOffscreen() {
  if (!chrome.offscreen || !chrome.runtime.getContexts) {
    return false;
  }
  const contexts = await chrome.runtime.getContexts({ contextTypes: ["OFFSCREEN_DOCUMENT"] });
  return contexts.length > 0;
}

export async function ensureOffscreen() {
  if (await hasOffscreen()) {
    return;
  }
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["CLIPBOARD", "IFRAME_SCRIPTING"],
    justification: "Clipboard commands and sandboxed loaded modules",
  });
}

export async function callOffscreen(message) {
  await ensureOffscreen();
  return chrome.runtime.sendMessage(message);
}
