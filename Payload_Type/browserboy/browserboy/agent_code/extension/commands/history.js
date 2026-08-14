export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const query = {
    text: args.query || args.text || "",
    maxResults: Number(args.max_results || args.maxResults || 100),
  };
  if (args.start_time) {
    query.startTime = Number(args.start_time);
  }
  if (args.end_time) {
    query.endTime = Number(args.end_time);
  }
  const items = await ctx.history.search(query);
  return JSON.stringify(
    items.map((item) => ({
      id: item.id,
      url: item.url,
      title: item.title,
      lastVisitTime: item.lastVisitTime,
      visitCount: item.visitCount,
      typedCount: item.typedCount,
    })),
    null,
    2,
  );
}
