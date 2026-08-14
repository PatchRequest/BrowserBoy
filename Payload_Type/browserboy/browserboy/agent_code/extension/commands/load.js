export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const name = args.name;
  const fileId = args.file_id;
  if (!name || !fileId) {
    throw new Error("load requires name and file_id");
  }
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
    throw new Error("load name must be a JS identifier");
  }
  const code = await ctx.downloadFile(fileId);
  if (!code.includes("export") || !code.includes("run")) {
    throw new Error("loaded file must export async function run(task, ctx)");
  }
  await ctx.registerLoaded(name, code);
  return {
    browserboy_response: {
      task_id: task.id,
      user_output: `loaded ${name}`,
      completed: true,
      commands: [{ action: "add", cmd: name }],
    },
  };
}
