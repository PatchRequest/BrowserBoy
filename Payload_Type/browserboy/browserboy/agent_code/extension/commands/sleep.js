export async function run(task, ctx) {
  const args = ctx.parseArgs(task);
  const interval = args.seconds ?? args.interval ?? args.sleep;
  const jitter = args.jitter;
  if (interval === undefined || interval === null) {
    throw new Error("sleep requires seconds");
  }
  return ctx.setSleep(interval, jitter);
}
