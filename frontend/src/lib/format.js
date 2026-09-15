// Format an ISO timestamp as a short relative string ("2h ago").
export function relativeTime(isoTimestamp) {
  if (!isoTimestamp) return "";
  const published = new Date(isoTimestamp);
  if (Number.isNaN(published.getTime())) return "";

  const seconds = (Date.now() - published.getTime()) / 1000;
  if (seconds < 0) return "just now";
  if (seconds < 3600) return `${Math.max(1, Math.floor(seconds / 60))}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
