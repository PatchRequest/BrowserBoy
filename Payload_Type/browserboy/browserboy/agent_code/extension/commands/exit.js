export async function run(_task, ctx) {
  await ctx.die();
  return "exited";
}
