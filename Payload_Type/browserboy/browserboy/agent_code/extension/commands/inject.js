export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  if (args.tab_id === undefined || !args.javascript) {
    throw new Error("inject requires tab_id and javascript");
  }
  const world = args.world === "ISOLATED" ? "ISOLATED" : "MAIN";
  const results = await ctx.scripting.executeScript({
    tabId: Number(args.tab_id),
    code: args.javascript,
    world,
  });
  return JSON.stringify(results, null, 2);
}
