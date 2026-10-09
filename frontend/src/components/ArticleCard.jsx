import { useState } from "react";
import { Link } from "react-router-dom";
import { relativeTime } from "../lib/format";
import ArticleActions from "./ArticleActions";
import RelatedArticles from "./RelatedArticles";
import ScoreBreakdown from "./ScoreBreakdown";

export default function ArticleCard({ article, categoryName, categoriesById, score = null, breakdown = null }) {
  // Live publishers' image URLs expire or block hotlinking; fall back to the
  // placeholder rather than showing a broken-image icon.
  const [imageFailed, setImageFailed] = useState(false);
  return (
    <article className="border-b border-line py-8 first:pt-0 last:border-b-0">
      <div className="flex gap-6">
        <Link to={`/articles/${article.id}`} className="hidden w-44 shrink-0 sm:block">
          <div className="aspect-[4/3] overflow-hidden rounded-sm bg-line">
            {article.image_url && !imageFailed ? (
              <img
                src={article.image_url}
                alt=""
                className="h-full w-full object-cover"
                loading="lazy"
                referrerPolicy="no-referrer"
                onError={() => setImageFailed(true)}
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brass-soft to-line">
                <span className="font-display text-base italic text-ink-faint">The Signal</span>
              </div>
            )}
          </div>
        </Link>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <span className="font-semibold uppercase tracking-wide text-signature">
              {categoryName || "General"}
            </span>
            <span className="text-ink-faint">·</span>
            <span className="font-mono text-ink-faint">{article.source_name}</span>
            {article.published_at && (
              <>
                <span className="text-ink-faint">·</span>
                <span className="font-mono text-ink-faint">{relativeTime(article.published_at)}</span>
              </>
            )}
          </div>

          <h3 className="mt-2 text-balance font-display text-2xl font-semibold leading-snug text-ink">
            <Link to={`/articles/${article.id}`} className="transition hover:text-signature">
              {article.title}
            </Link>
          </h3>

          {article.description && (
            <p className="mt-2 line-clamp-3 text-[15px] leading-relaxed text-ink-soft">{article.description}</p>
          )}

          <div className="mt-4">
            <ArticleActions articleId={article.id} />
          </div>

          <div className="mt-3 flex flex-wrap gap-6 text-xs">
            <ScoreBreakdown score={score} breakdown={breakdown} />
            <RelatedArticles articleId={article.id} categoriesById={categoriesById} />
          </div>
        </div>
      </div>
    </article>
  );
}
