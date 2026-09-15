import * as api from "../api/client";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function TrendingWidget() {
  const { dataVersion } = useApp();
  const { data, loading } = useApi(() => api.getTrending(5), [dataVersion]);

  return (
    <div className="lg:sticky lg:top-8">
      <h2 className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-ink-faint">
        Trending now
      </h2>
      <div className="rule mt-3" />
      {loading && <p className="mt-4 text-sm text-ink-faint">Loading…</p>}
      {data && data.topics.length === 0 && (
        <p className="mt-4 text-sm text-ink-faint">Nothing trending in the last 24 hours yet.</p>
      )}
      <ol className="mt-4 space-y-4">
        {data?.topics.map((t, i) => (
          <li key={t.topic} className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-brass tabular">{String(i + 1).padStart(2, "0")}</span>
            <span className="text-sm font-medium capitalize leading-snug text-ink">{t.topic}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
