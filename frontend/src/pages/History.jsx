import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function History() {
  const { categoriesById, dataVersion } = useApp();
  const { data, loading, error } = useApi(() => api.getHistory(api.DEFAULT_USER_ID), [dataVersion]);

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-semibold">History</h1>
      <p className="mt-1 text-sm text-ink-faint">Articles you've marked as read.</p>

      <div className="mt-8">
        {loading && <p className="text-ink-faint">Loading…</p>}
        {error && <p className="text-bad">Could not load your history.</p>}
        {data?.articles.length === 0 && <p className="text-ink-faint">No reading history yet.</p>}
        {data?.articles.map((a) => (
          <ArticleCard key={a.id} article={a} categoryName={categoriesById[a.category_id]} categoriesById={categoriesById} />
        ))}
      </div>
    </section>
  );
}
