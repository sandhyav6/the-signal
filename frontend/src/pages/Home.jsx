import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import TrendingWidget from "../components/TrendingWidget";
import { useApp } from "../lib/AppContext";
import { useApi } from "../lib/useApi";

export default function Home() {
  const { categoriesById, dataVersion } = useApp();
  const { data: feed, loading, error } = useApi(
    () => api.getFeed(api.DEFAULT_USER_ID, "foryou"),
    [dataVersion],
  );

  return (
    <div className="grid grid-cols-1 gap-16 lg:grid-cols-[1fr_260px]">
      <section>
        <h1 className="font-display text-4xl font-semibold">For You</h1>
        <p className="mt-1 text-sm text-ink-faint">Ranked for you — expand any story to see exactly why.</p>

        <div className="mt-8">
          {loading && <p className="text-ink-faint">Loading your feed…</p>}
          {error && <p className="text-bad">Could not load the feed. Is the backend running?</p>}
          {feed?.articles.length === 0 && (
            <p className="text-ink-faint">No articles yet — try Refresh feed above.</p>
          )}
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

      <aside>
        <TrendingWidget />
      </aside>
    </div>
  );
}
