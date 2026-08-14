export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const name = args.name;
  if (!name) {
    const names = ctx.listLoaded();
    return names.length ? names.join("\n") : "no loaded commands";
  }
  const innerTask = {
    id: task.id,
    command: name,
    parameters: args.args || args.parameters || {},
  };
  const result = await ctx.runLoaded(name, innerTask);
  return result;
}
