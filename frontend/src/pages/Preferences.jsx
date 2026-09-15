import { useEffect, useState } from "react";
import * as api from "../api/client";
import { useApp } from "../lib/AppContext";

export default function Preferences() {
  const { categories } = useApp();
  const [weights, setWeights] = useState({});
  const [loaded, setLoaded] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (categories.length === 0) return;
    api.getPreferences(api.DEFAULT_USER_ID).then((response) => {
      const prefs = response.preferences;
      setWeights(Object.fromEntries(categories.map((c) => [c.id, Number(prefs[c.id] ?? 0.1)])));
      setLoaded(true);
    });
  }, [categories]);

  const save = async () => {
    setSaving(true);
    try {
      await api.putPreferences(api.DEFAULT_USER_ID, weights);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="font-display text-4xl font-semibold">Preferences</h1>
      <p className="mt-1 text-sm text-ink-faint">
        Adjust how interested you are in each category — 0 is not interested, 1 is very interested.
      </p>

      {!loaded && <p className="mt-8 text-ink-faint">Loading…</p>}

      {loaded && (
        <>
          <div className="mt-10 space-y-7">
            {categories.map((c) => (
              <div key={c.id}>
                <div className="flex items-baseline justify-between">
                  <label htmlFor={`pref-${c.id}`} className="font-medium text-ink">
                    {c.name}
                  </label>
                  <span className="font-mono text-sm text-ink-faint tabular">
                    {(weights[c.id] ?? 0.1).toFixed(2)}
                  </span>
                </div>
                <input
                  id={`pref-${c.id}`}
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[c.id] ?? 0.1}
                  onChange={(e) => setWeights((w) => ({ ...w, [c.id]: Number(e.target.value) }))}
                  className="mt-2 w-full accent-signature"
                />
              </div>
            ))}
          </div>

          <div className="mt-10 flex items-center gap-4">
            <button
              onClick={save}
              disabled={saving}
              className="rounded-full bg-signature px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-signature-ink disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save preferences"}
            </button>
            {saved && <span className="text-sm text-good">Preferences updated.</span>}
          </div>
        </>
      )}
    </section>
  );
}
