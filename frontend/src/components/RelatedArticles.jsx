import { useState } from "react";
import * as api from "../api/client";
import { IconChevron } from "./Icon";

// Related articles are fetched lazily, only once the reader actually asks
// for them, rather than for every card the moment the page loads.
export default function RelatedArticles({ articleId, categoriesById }) {
  const [open, setOpen] = useState(false);
  const [related, setRelated] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next && related === null) {
      setLoading(true);
      try {
        const detail = await api.getArticle(articleId);
        setRelated(detail.related || []);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div>
      <button
        onClick={toggle}
        className="flex items-center gap-1 font-medium text-ink-faint transition hover:text-ink"
      >
        Related articles
        <IconChevron className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <ul className="mt-2 space-y-1.5 border-l-2 border-brass-soft pl-3">
          {loading && <li className="text-ink-faint">Loading…</li>}
          {!loading && related?.length === 0 && <li className="text-ink-faint">No related articles found.</li>}
          {related?.map((r) => (
            <li key={r.id} className="text-ink-soft">
              <span className="font-medium text-ink">{r.title}</span>
              {categoriesById?.[r.category_id] && (
                <span className="text-ink-faint"> — {categoriesById[r.category_id]}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
