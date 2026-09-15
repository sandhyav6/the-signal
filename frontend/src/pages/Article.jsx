import { Link, useParams } from "react-router-dom";
import * as api from "../api/client";
import ArticleActions from "../components/ArticleActions";
import ArticleCard from "../components/ArticleCard";
import { useApp } from "../lib/AppContext";
import { relativeTime } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function Article() {
  const { id } = useParams();
  const { categoriesById, dataVersion } = useApp();
  const { data, loading, error } = useApi(() => api.getArticle(id), [id, dataVersion]);

  if (loading) return <p className="text-ink-faint">Loading…</p>;
  if (error) return <p className="text-bad">Could not load this article. Is the backend running?</p>;
  if (!data) return null;

  const { article, related } = data;

  return (
    <article className="mx-auto max-w-2xl">
      <Link to="/" className="text-sm font-medium text-ink-faint transition hover:text-signature">
        ← Back to feed
      </Link>

      <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-signature">
        {categoriesById[article.category_id] || "Uncategorized"}
      </div>
      <h1 className="mt-2 text-balance font-display text-4xl font-semibold leading-tight text-ink sm:text-5xl">
        {article.title}
      </h1>
      <div className="mt-4 font-mono text-xs text-ink-faint">
        {article.source_name}
        {article.author ? ` · ${article.author}` : ""} · {relativeTime(article.published_at)}
      </div>

      {article.image_url && (
        <img src={article.image_url} alt="" className="mt-8 aspect-video w-full rounded-sm object-cover" />
      )}

      {article.description && (
        <p className="mt-8 text-lg leading-relaxed text-ink-soft">{article.description}</p>
      )}

      <div className="mt-8 border-y border-line py-4">
        <ArticleActions articleId={article.id} />
      </div>

      {related.length > 0 && (
        <div className="mt-14">
          <h2 className="font-display text-2xl font-semibold">Related</h2>
          <div className="mt-4">
            {related.map((r) => (
              <ArticleCard key={r.id} article={r} categoryName={categoriesById[r.category_id]} categoriesById={categoriesById} />
            ))}
          </div>
        </div>
      )}
    </article>
  );
}
