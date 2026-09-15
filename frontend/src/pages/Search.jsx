import { useEffect, useState } from "react";
import * as api from "../api/client";
import ArticleCard from "../components/ArticleCard";
import { IconSearch } from "../components/Icon";
import { useApp } from "../lib/AppContext";

export default function Search() {
  const { categoriesById, dataVersion } = useApp();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [results, setResults] = useState(null);

  // Debounced autocomplete — one request ~150ms after the user stops typing.
  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      return undefined;
    }
    const id = setTimeout(() => {
      api.suggest(query).then((r) => setSuggestions(r.suggestions)).catch(() => setSuggestions([]));
    }, 150);
    return () => clearTimeout(id);
  }, [query]);

  // Debounced search — a slightly longer delay than suggestions. Re-runs on
  // dataVersion too, so results reflect a like/save/etc. made in the meantime.
  useEffect(() => {
    if (!query.trim()) {
      setResults(null);
      return undefined;
    }
    const id = setTimeout(() => {
      api.search(query).then(setResults).catch(() => setResults(null));
    }, 300);
    return () => clearTimeout(id);
  }, [query, dataVersion]);

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-semibold">Search</h1>

      <div className="relative mt-6">
        <IconSearch className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search headlines and descriptions…"
          className="w-full rounded-full border border-line-strong bg-paper-raised py-3 pl-11 pr-4 text-[15px] text-ink outline-none transition focus:border-signature"
        />
      </div>

      {suggestions.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.slice(0, 8).map((s) => (
            <button
              key={s}
              onClick={() => setQuery(s)}
              className="rounded-full bg-brass-soft px-3 py-1 text-xs font-medium text-signature-ink transition hover:bg-signature-soft"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="mt-8">
        {!query.trim() && <p className="text-ink-faint">Type to search article titles and descriptions.</p>}
        {results && <p className="mb-4 font-mono text-xs text-ink-faint tabular">{results.total} result(s)</p>}
        {results?.articles.map((a) => (
          <ArticleCard key={a.id} article={a} categoryName={categoriesById[a.category_id]} categoriesById={categoriesById} />
        ))}
      </div>
    </section>
  );
}
