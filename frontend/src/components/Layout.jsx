import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useApp } from "../lib/AppContext";

const NAV_ITEMS = [
  { to: "/", label: "For You", end: true },
  { to: "/latest", label: "Latest" },
  { to: "/trending", label: "Trending" },
  { to: "/categories", label: "Categories" },
  { to: "/search", label: "Search" },
  { to: "/saved", label: "Saved" },
  { to: "/history", label: "History" },
  { to: "/preferences", label: "Preferences" },
];

// What the badge says about where the stories on screen came from.
const SOURCE_LABELS = {
  live: { text: "Live", className: "bg-good" },
  cache: { text: "Stored", className: "bg-brass" },
  mock: { text: "Sample data", className: "bg-ink-faint" },
};

function SourceBadge({ source, message }) {
  const label = SOURCE_LABELS[source];
  if (!label) return null;
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs text-ink-faint" title={message || undefined}>
      <span className={`h-1.5 w-1.5 rounded-full ${label.className}`} aria-hidden="true" />
      {label.text}
    </span>
  );
}

export default function Layout() {
  const { mode, setMode, status, refresh, lastRefresh, refreshResult, hasNewStories, showNewStories } = useApp();
  const liveAvailable = status?.live_available ?? false;
  const source = refreshResult?.source ?? status?.last_source ?? (mode === "mock" ? "mock" : null);
  const notice = refreshResult?.message ?? status?.last_message;
  const [refreshing, setRefreshing] = useState(false);
  const [secondsAgo, setSecondsAgo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!lastRefresh) return undefined;
    const tick = () => setSecondsAgo(Math.floor((Date.now() - lastRefresh.getTime()) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [lastRefresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refresh();
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="border-b border-line bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 pb-4 pt-6">
          <NavLink to="/" className="font-display text-[1.75rem] font-semibold tracking-tight text-ink">
            The Signal
          </NavLink>

          <div className="flex items-center gap-4">
            <div className="hidden text-right leading-tight sm:block">
              <SourceBadge source={source} message={notice} />
              {refreshResult && (
                <p className="font-mono text-xs text-ink-faint">
                  <span className="tabular">+{refreshResult.added}</span> new
                  {secondsAgo !== null && <span className="tabular"> · {secondsAgo}s ago</span>}
                </p>
              )}
              {error && <p className="text-xs text-bad">{error}</p>}
            </div>

            <div className="flex items-center rounded-full border border-line-strong p-0.5 text-xs font-medium">
              {["mock", "live"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  disabled={m === "live" && !liveAvailable}
                  title={m === "live" && !liveAvailable ? "Add NEWS_API_KEY to .env to enable live news" : undefined}
                  aria-pressed={mode === m}
                  className={`rounded-full px-3 py-1 capitalize transition disabled:cursor-not-allowed disabled:opacity-40 ${
                    mode === m ? "bg-ink text-paper" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="rounded-full bg-signature px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-signature-ink disabled:opacity-50"
            >
              {refreshing ? "Refreshing…" : "Refresh feed"}
            </button>
          </div>
        </div>

        <nav className="scrollbar-none mx-auto flex max-w-6xl gap-6 overflow-x-auto px-6 text-sm">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `whitespace-nowrap border-b-2 py-3 font-medium transition ${
                  isActive ? "border-signature text-ink" : "border-transparent text-ink-faint hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      {(notice || hasNewStories) && (
        <div className="mx-auto mt-4 flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 text-sm">
          {notice ? <p className="text-ink-soft">{notice}</p> : <span />}
          {hasNewStories && (
            <button
              onClick={showNewStories}
              className="rounded-full border border-signature px-4 py-1 text-xs font-semibold text-signature transition hover:bg-signature hover:text-white"
            >
              New stories available — show them
            </button>
          )}
        </div>
      )}

      <main className="mx-auto max-w-6xl px-6 py-10">
        <Outlet />
      </main>

      <footer className="mx-auto max-w-6xl border-t border-line px-6 py-8 text-xs text-ink-faint">
        The Signal — a DAA project feed-ranking engine, not a wire service.
        {source === "live" && (
          <>
            {" "}Headlines powered by{" "}
            <a href="https://newsapi.org" target="_blank" rel="noreferrer" className="underline hover:text-ink">
              NewsAPI.org
            </a>
            ; every story links to its original publisher.
          </>
        )}
      </footer>
    </div>
  );
}
