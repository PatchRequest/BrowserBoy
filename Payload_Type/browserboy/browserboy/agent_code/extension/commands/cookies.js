function netscapeLine(cookie) {
  const domain = cookie.domain || "";
  const includeSub = domain.startsWith(".") ? "TRUE" : "FALSE";
  const path = cookie.path || "/";
  const secure = cookie.secure ? "TRUE" : "FALSE";
  const expiry = cookie.expirationDate ? Math.trunc(cookie.expirationDate) : 0;
  return [domain, includeSub, path, secure, expiry, cookie.name, cookie.value].join("\t");
}

export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const action = args.action || "list";
  if (action === "get") {
    if (!args.url || !args.name) {
      throw new Error("cookies get requires url and name");
    }
    const cookie = await ctx.cookies.get({ url: args.url, name: args.name });
    return JSON.stringify(cookie, null, 2);
  }
  if (action !== "list" && action !== "export") {
    throw new Error(`unknown cookies action: ${action}`);
  }
  const filter = {};
  if (args.domain) {
    filter.domain = args.domain;
  }
  if (args.url) {
    filter.url = args.url;
  }
  if (args.name) {
    filter.name = args.name;
  }
  const cookies = await ctx.cookies.getAll(filter);
  const format = args.format || "json";
  if (format === "netscape") {
    const lines = ["# Netscape HTTP Cookie File", ...cookies.map(netscapeLine)];
    return lines.join("\n");
  }
  return JSON.stringify(cookies, null, 2);
}
