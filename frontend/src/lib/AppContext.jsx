import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as api from "../api/client";

const AppContext = createContext(null);

// Global, app-wide state: the category list (fetched once, needed almost
// everywhere for name lookups), the mock/live mode toggle, the
// refresh-feed result + timestamp that power the masthead's dynamic-feed
// indicator, and `dataVersion` — a counter every page's data-fetching
// depends on. Bumping it (after a refresh or any like/dislike/save/read)
// makes whichever page is currently mounted re-fetch automatically,
// without the user ever needing to reload or click Refresh themselves.
export function AppProvider({ children }) {
  const [categories, setCategories] = useState([]);
  const [mode, setMode] = useState("mock");
  const [lastRefresh, setLastRefresh] = useState(null);
  const [refreshResult, setRefreshResult] = useState(null);
  const [dataVersion, setDataVersion] = useState(0);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
  }, []);

  const categoriesById = Object.fromEntries(categories.map((c) => [c.id, c.name]));

  const bumpDataVersion = useCallback(() => setDataVersion((v) => v + 1), []);

  const refresh = useCallback(async () => {
    const result = await api.postRefresh(mode);
    setRefreshResult(result);
    setLastRefresh(new Date());
    bumpDataVersion();
    return result;
  }, [mode, bumpDataVersion]);

  const value = {
    categories,
    categoriesById,
    mode,
    setMode,
    lastRefresh,
    refreshResult,
    refresh,
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
