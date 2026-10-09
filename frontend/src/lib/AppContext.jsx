import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import * as api from "../api/client";

const AppContext = createContext(null);

// How often to ask the backend whether a background refresh brought in
// new stories (live mode refreshes itself on a timer — see
// backend/services/scheduler.py).
const STATUS_POLL_MS = 60_000;

// Global, app-wide state: the category list (fetched once, needed almost
// everywhere for name lookups), the mock/live mode toggle, the data-source
// status from GET /status, the refresh-feed result + timestamp that power
// the masthead's dynamic-feed indicator, and `dataVersion` — a counter
// every page's data-fetching depends on. Bumping it (after a refresh or
// any like/dislike/save/read) makes whichever page is currently mounted
// re-fetch automatically, without the user ever needing to reload.
export function AppProvider({ children }) {
  const [categories, setCategories] = useState([]);
  const [mode, setMode] = useState("mock");
  const [status, setStatus] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [refreshResult, setRefreshResult] = useState(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [hasNewStories, setHasNewStories] = useState(false);
  // Article count as of the last time the visible pages loaded data.
  const seenCount = useRef(null);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const next = await api.getStatus();
      setStatus(next);
      if (seenCount.current === null) seenCount.current = next.article_count;
      else if (next.article_count > seenCount.current) setHasNewStories(true);
      return next;
    } catch {
      return null;
    }
  }, []);

  // First status load also picks the toggle's starting position.
  useEffect(() => {
    loadStatus().then((s) => s && setMode(s.default_mode));
    const id = setInterval(loadStatus, STATUS_POLL_MS);
    return () => clearInterval(id);
  }, [loadStatus]);

  const categoriesById = Object.fromEntries(categories.map((c) => [c.id, c.name]));

  const bumpDataVersion = useCallback(() => setDataVersion((v) => v + 1), []);

  const showNewStories = useCallback(async () => {
    const s = await loadStatus();
    if (s) seenCount.current = s.article_count;
    setHasNewStories(false);
    bumpDataVersion();
  }, [loadStatus, bumpDataVersion]);

  const refresh = useCallback(async () => {
    const result = await api.postRefresh(mode);
    setRefreshResult(result);
    setLastRefresh(new Date());
    await showNewStories();
    return result;
  }, [mode, showNewStories]);

  const value = {
    categories,
    categoriesById,
    mode,
    setMode,
    status,
    lastRefresh,
    refreshResult,
    refresh,
    hasNewStories,
    showNewStories,
    dataVersion,
    bumpDataVersion,
  };
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within an AppProvider");
  return ctx;
}
