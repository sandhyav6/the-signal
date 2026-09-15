import { useState } from "react";
import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function Categories() {
  const { categories, categoriesById, dataVersion } = useApp();
  const [selectedId, setSelectedId] = useState(null);
  const { data: feed, loading } = useApi(
    () => (selectedId ? api.getFeed(api.DEFAULT_USER_ID, "category", selectedId) : Promise.resolve(null)),
    [selectedId, dataVersion],
  );

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-semibold">Categories</h1>

      <div className="mt-6 flex flex-wrap gap-2">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedId(c.id)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
              selectedId === c.id
                ? "border-signature bg-signature text-white"
                : "border-line-strong text-ink-soft hover:border-signature hover:text-signature"
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      <div className="mt-8">
        {!selectedId && <p className="text-ink-faint">Pick a category above to see its feed.</p>}
        {loading && <p className="text-ink-faint">Loading…</p>}
        {feed?.articles.length === 0 && <p className="text-ink-faint">No articles in this category yet.</p>}
        {feed?.articles.map((entry) => (
          <ArticleCard
            key={entry.article.id}
            article={entry.article}
            categoryName={categoriesById[entry.article.category_id]}
            categoriesById={categoriesById}
            score={entry.score}
            breakdown={entry.breakdown}
          />
        ))}
      </div>
    </section>
  );
}
