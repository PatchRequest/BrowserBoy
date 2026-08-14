export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const query = {};
  if (args.query) {
    query.query = [args.query];
  }
  if (args.limit) {
    query.limit = Number(args.limit);
  }
  if (args.state) {
    query.state = args.state;
  }
  const items = await ctx.downloads.search(query);
  return JSON.stringify(
    items.map((item) => ({
      id: item.id,
      url: item.url,
      filename: item.filename,
      state: item.state,
      danger: item.danger,
      startTime: item.startTime,
      bytesReceived: item.bytesReceived,
      totalBytes: item.totalBytes,
    })),
    null,
    2,
  );
}
