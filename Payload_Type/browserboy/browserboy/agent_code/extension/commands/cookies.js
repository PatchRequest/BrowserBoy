function netscapeLine(cookie) {
  const domain = cookie.domain || "";
  const includeSub = domain.startsWith(".") ? "TRUE" : "FALSE";
  const path = cookie.path || "/";
  const secure = cookie.secure ? "TRUE" : "FALSE";
  const expiry = cookie.expirationDate ? Math.trunc(cookie.expirationDate) : 0;
  return [domain, includeSub, path, secure, expiry, cookie.name, cookie.value].join("\t");
}

function cookieKey(cookie) {
  const partition = cookie.partitionKey?.topLevelSite || "";
  return [cookie.storeId, cookie.domain, cookie.path, cookie.name, partition].join("|");
}

async function collectCookies(ctx, filter) {
  let stores = [];
  try {
    stores = await ctx.cookies.getAllCookieStores();
  } catch {
    stores = [];
  }
  if (!Array.isArray(stores) || stores.length === 0) {
    return ctx.cookies.getAll(filter);
  }
  const seen = new Set();
  const out = [];
  for (const store of stores) {
    const batch = await ctx.cookies.getAll({ ...filter, storeId: store.id });
    for (const cookie of batch) {
      const key = cookieKey(cookie);
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      out.push(cookie);
    }
  }
  return out;
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
  const cookies = await collectCookies(ctx, filter);
  const format = args.format || "json";
  if (format === "netscape") {
    const lines = ["# Netscape HTTP Cookie File", ...cookies.map(netscapeLine)];
    return lines.join("\n");
  }
  return JSON.stringify(cookies, null, 2);
}
