export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const action = args.action || "read";
  if (action === "write") {
    if (args.text === undefined) {
      throw new Error("clipboard write requires text");
    }
    await ctx.clipboard.write(args.text);
    return "wrote clipboard";
  }
  if (action !== "read") {
    throw new Error(`unknown clipboard action: ${action}`);
  }
  return await ctx.clipboard.read();
}
