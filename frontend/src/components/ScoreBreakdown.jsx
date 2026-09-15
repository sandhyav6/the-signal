import { useState } from "react";
import { IconChevron } from "./Icon";

const LABELS = {
  interest: "Matches your interests",
  recency: "Recently published",
  popularity: "Popular",
  keyword_relevance: "Matches your search",
  repetition_penalty: "Diversity adjustment",
};

// Renders one article's ranking explanation, collapsed by default.
export default function ScoreBreakdown({ score, breakdown }) {
  const [open, setOpen] = useState(false);
  if (score == null || !breakdown) return null;

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 font-medium text-ink-faint transition hover:text-ink"
      >
        Why this is here
        <IconChevron className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <dl className="mt-2 space-y-1 border-l-2 border-brass-soft pl-3">
          {Object.entries(LABELS).map(([key, label]) => {
            const term = breakdown[key];
            if (!term || term.contribution === 0) return null;
            return (
              <div key={key} className="flex justify-between gap-4 font-mono">
                <dt className="text-ink-soft">{label}</dt>
                <dd className={`tabular ${term.contribution >= 0 ? "text-good" : "text-bad"}`}>
                  {term.contribution >= 0 ? "+" : ""}
                  {term.contribution.toFixed(1)}
                </dd>
              </div>
            );
          })}
          <div className="flex justify-between gap-4 border-t border-line pt-1 font-mono font-semibold">
            <dt>Final score</dt>
            <dd className="tabular">{score.toFixed(1)}</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
