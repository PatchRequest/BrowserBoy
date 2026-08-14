import { base64ToBytes } from "../lib/bytes.js";

export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  let windowId = args.window_id;
  if (args.tab_id !== undefined) {
    const tab = await ctx.tabs.get(Number(args.tab_id));
    windowId = tab.windowId;
    if (!tab.active) {
      await ctx.tabs.update(tab.id, { active: true });
    }
  }
  const dataUrl = await ctx.tabs.captureVisibleTab(windowId, { format: "png" });
  if (!dataUrl || !dataUrl.includes(",")) {
    throw new Error("screenshot failed");
  }
  const bytes = base64ToBytes(dataUrl.split(",")[1]);
  const filename = args.filename || `screenshot-${Date.now()}.png`;
  const fileId = await ctx.uploadScreenshot(bytes, filename);
  return `screenshot stored as ${fileId}`;
}
