function flatten(nodes, acc = []) {
  for (const node of nodes) {
    acc.push({
      id: node.id,
      title: node.title,
      url: node.url || "",
      parentId: node.parentId,
      folder: !node.url,
    });
    if (node.children) {
      flatten(node.children, acc);
    }
  }
  return acc;
}

export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const action = args.action || (args.query ? "search" : "list");
  if (action === "search") {
    const items = await ctx.bookmarks.search(args.query || "");
    return JSON.stringify(
      items.map((item) => ({
        id: item.id,
        title: item.title,
        url: item.url || "",
        folder: !item.url,
      })),
      null,
      2,
    );
  }
  if (action !== "list") {
    throw new Error(`unknown bookmarks action: ${action}`);
  }
  const tree = await ctx.bookmarks.getTree();
  return JSON.stringify(flatten(tree), null, 2);
}
