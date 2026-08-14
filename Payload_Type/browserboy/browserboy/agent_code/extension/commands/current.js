export async function run(_task, ctx) {
  const tabs = await ctx.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length) {
    return "no active tab";
  }
  const tab = tabs[0];
  return JSON.stringify(
    {
      id: tab.id,
      windowId: tab.windowId,
      url: tab.url,
      title: tab.title,
      incognito: tab.incognito,
    },
    null,
    2,
  );
}
