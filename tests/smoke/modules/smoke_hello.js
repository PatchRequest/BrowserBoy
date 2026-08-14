export async function run(task, ctx) {
  const tabs = await ctx.tabs.query({});
  return `smoke-hello:${tabs.length}`;
}
