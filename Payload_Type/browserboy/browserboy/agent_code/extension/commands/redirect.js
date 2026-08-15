export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const action = args.action || "list";
  if (action === "list") {
    return JSON.stringify(await ctx.redirect.list(), null, 2);
  }
  if (action === "add") {
    const record = await ctx.redirect.add(args);
    return JSON.stringify(record, null, 2);
  }
  if (action === "remove") {
    const id = args.id ?? args.rule_id;
    const removed = await ctx.redirect.remove(id);
    return `removed ${removed}`;
  }
  if (action === "clear") {
    const count = await ctx.redirect.clear();
    return `cleared ${count}`;
  }
  throw new Error(`unknown redirect action: ${action}`);
}
