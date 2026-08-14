export function nextDelayMs(intervalSec, jitterPercent, random = Math.random) {
  const interval = Number(intervalSec);
  const jitter = Number(jitterPercent);
  const safeInterval = Number.isFinite(interval) && interval > 0 ? interval : 10;
  const safeJitter = Number.isFinite(jitter) && jitter > 0 ? Math.min(jitter, 100) : 0;
  const spread = safeInterval * (safeJitter / 100);
  const offset = spread === 0 ? 0 : (random() * 2 - 1) * spread;
  return Math.max(1000, Math.round((safeInterval + offset) * 1000));
}

export function killdatePassed(killdate, now = new Date()) {
  if (!killdate) {
    return false;
  }
  const match = String(killdate).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) {
    return false;
  }
  const end = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 23, 59, 59));
  return now.getTime() >= end.getTime();
}

export function sleepInfo(intervalSec, jitterPercent) {
  return `${Number(intervalSec) || 0}s:${Number(jitterPercent) || 0}%`;
}
