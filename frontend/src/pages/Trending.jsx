import { useState } from "react";
import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function Trending() {
  const { categoriesById, dataVersion } = useApp();
  const { data, loading } = useApi(() => api.getTrending(10), [dataVersion]);
  const [selected, setSelected] = useState(null);
  const { data: results } = useApi(
    () => (selected ? api.search(selected) : Promise.resolve(null)),
    [selected, dataVersion],
  );

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-semibold">Trending</h1>
      <p className="mt-1 text-sm text-ink-faint">Ranked by recent mentions, recency, and engagement.</p>

      {loading && <p className="mt-8 text-ink-faint">Loading…</p>}
      {data && data.topics.length === 0 && (
        <p className="mt-8 text-ink-faint">Nothing trending in the last 24 hours yet.</p>
      )}

      <ol className="rule mt-8 divide-y divide-line">
        {data?.topics.map((t, i) => (
          <li key={t.topic}>
            <button
              onClick={() => setSelected(t.topic)}
              className={`flex w-full items-baseline gap-4 py-4 text-left transition hover:bg-paper-raised ${
                selected === t.topic ? "text-signature" : "text-ink"
              }`}
            >
              <span className="font-mono text-lg text-brass tabular">{String(i + 1).padStart(2, "0")}</span>
              <span className="flex-1 font-display text-xl font-medium capitalize">{t.topic}</span>
              <span className="font-mono text-xs text-ink-faint tabular">score {t.score.toFixed(1)}</span>
            </button>
          </li>
        ))}
      </ol>

      {selected && (
        <div className="mt-10">
          <h2 className="font-display text-2xl font-semibold capitalize">Stories about {selected}</h2>
          <div className="mt-6">
            {results?.articles.length === 0 && <p className="text-ink-faint">No matching articles found.</p>}
            {results?.articles.map((a) => (
              <ArticleCard key={a.id} article={a} categoryName={categoriesById[a.category_id]} categoriesById={categoriesById} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
