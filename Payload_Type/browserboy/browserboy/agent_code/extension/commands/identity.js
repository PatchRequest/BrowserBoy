export async function run(_task, ctx) {
  let user = {};
  let platform = {};
  try {
    user = await ctx.identity.getProfileUserInfo();
  } catch (error) {
    user = { error: error instanceof Error ? error.message : String(error) };
  }
  try {
    platform = await ctx.runtime.getPlatformInfo();
  } catch (error) {
    platform = { error: error instanceof Error ? error.message : String(error) };
  }
  return JSON.stringify(
    {
      user,
      platform,
      extension_id: ctx.runtime.id,
    },
    null,
    2,
  );
}
