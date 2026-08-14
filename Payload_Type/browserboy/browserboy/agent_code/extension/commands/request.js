export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  if (!args.url) {
    throw new Error("request requires url");
  }
  let headers = args.headers || {};
  if (typeof headers === "string") {
    headers = JSON.parse(headers);
  }
  const result = await ctx.request({
    url: args.url,
    method: args.method || "GET",
    headers,
    body: args.body,
  });
  return JSON.stringify(result, null, 2);
}
