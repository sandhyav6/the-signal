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

export default function Layout() {
  const { mode, setMode, refresh, lastRefresh, refreshResult } = useApp();
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
                  className={`rounded-full px-3 py-1 capitalize transition ${
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

      <main className="mx-auto max-w-6xl px-6 py-10">
        <Outlet />
      </main>

      <footer className="mx-auto max-w-6xl border-t border-line px-6 py-8 text-xs text-ink-faint">
        The Signal — a DAA project feed-ranking engine, not a wire service.
      </footer>
    </div>
  );
}
