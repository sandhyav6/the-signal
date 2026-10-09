// The backend stores and sends naive UTC timestamps ("2026-10-09T12:00:00"
// with no "Z"). JavaScript would parse those as *local* time, skewing every
// relative label by the viewer's UTC offset, so mark them as UTC first.
export function parseTimestamp(isoTimestamp) {
  if (!isoTimestamp) return null;
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(isoTimestamp);
  const parsed = new Date(hasZone ? isoTimestamp : `${isoTimestamp}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

// Format an ISO timestamp as a short relative string ("2h ago").
export function relativeTime(isoTimestamp) {
  const published = parseTimestamp(isoTimestamp);
  if (!published) return "";

  const seconds = (Date.now() - published.getTime()) / 1000;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

// Host name of a URL without "www." ("reuters.com"), or "" if unparseable.
export function hostName(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}
