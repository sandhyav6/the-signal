import { useCallback, useEffect, useState } from "react";

// Wraps an async fetcher with loading/error/data state and a manual reload.
// `deps` follows useCallback's own rules — pass the values the fetcher
// closes over so it re-runs when they change.
export function useApi(fetcher, deps) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => load(), [load]);

  return { data, error, loading, reload: load };
}
