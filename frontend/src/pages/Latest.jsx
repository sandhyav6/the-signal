import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function Latest() {
  const { categoriesById, dataVersion } = useApp();
  const { data: feed, loading, error } = useApi(
    () => api.getFeed(api.DEFAULT_USER_ID, "latest"),
    [dataVersion],
  );

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-semibold">Latest</h1>
      <p className="mt-1 text-sm text-ink-faint">Straight chronological order — no personalization.</p>

      <div className="mt-8">
        {loading && <p className="text-ink-faint">Loading…</p>}
        {error && <p className="text-bad">Could not load the feed.</p>}
        {feed?.articles.map((entry) => (
          <ArticleCard
            key={entry.article.id}
            article={entry.article}
            categoryName={categoriesById[entry.article.category_id]}
            categoriesById={categoriesById}
          />
        ))}
      </div>
    </section>
  );
}
