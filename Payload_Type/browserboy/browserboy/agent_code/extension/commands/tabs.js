export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const action = args.action || "list";
  if (action === "list") {
    const tabs = await ctx.tabs.query(args.query || {});
    return JSON.stringify(
      tabs.map((tab) => ({
        id: tab.id,
        windowId: tab.windowId,
        url: tab.url,
        title: tab.title,
        active: tab.active,
        highlighted: tab.highlighted,
        incognito: tab.incognito,
        pinned: tab.pinned,
      })),
      null,
      2,
    );
  }
  if (action === "create") {
    if (!args.url) {
      throw new Error("tabs create requires url");
    }
    const tab = await ctx.tabs.create({ url: args.url, active: Boolean(args.active) });
    return JSON.stringify({ id: tab.id, url: tab.url }, null, 2);
  }
  if (action === "close") {
    if (args.tab_id === undefined) {
      throw new Error("tabs close requires tab_id");
    }
    await ctx.tabs.remove(Number(args.tab_id));
    return `closed ${args.tab_id}`;
  }
  if (action === "update") {
    if (args.tab_id === undefined) {
      throw new Error("tabs update requires tab_id");
    }
    const props = {};
    if (args.url) {
      props.url = args.url;
    }
    if (args.active !== undefined) {
      props.active = Boolean(args.active);
    }
    const tab = await ctx.tabs.update(Number(args.tab_id), props);
    return JSON.stringify({ id: tab.id, url: tab.url, active: tab.active }, null, 2);
  }
  if (action === "reload") {
    if (args.tab_id === undefined) {
      throw new Error("tabs reload requires tab_id");
    }
    await ctx.tabs.reload(Number(args.tab_id), {});
    return `reloaded ${args.tab_id}`;
  }
  throw new Error(`unknown tabs action: ${action}`);
}
