import { useState } from "react";
import * as api from "../api/client";
import { useApp } from "../lib/AppContext";
import { IconBookmark } from "./Icon";

const ACTIONS = [
  { type: "like", label: "Like" },
  { type: "dislike", label: "Not interested" },
  { type: "save", label: "Save" },
  { type: "read", label: "Mark read" },
];

// The Like/Dislike/Save/Mark-read row, shared by ArticleCard and the full
// article page. Every action bumps the app-wide data version, which is
// what makes the feed re-rank itself immediately afterward instead of
// requiring a manual refresh — see lib/AppContext.jsx.
export default function ArticleActions({ articleId }) {
  const { bumpDataVersion } = useApp();
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const act = async (type) => {
    setBusy(type);
    try {
      if (type === "save") {
        await api.postBookmark(api.DEFAULT_USER_ID, articleId);
        setSaved(true);
      }
      await api.postInteraction(api.DEFAULT_USER_ID, articleId, type);
      setFeedback(type === "dislike" ? "Noted." : "Done.");
      bumpDataVersion();
      setTimeout(() => setFeedback(null), 1500);
    } catch {
      setFeedback("Could not reach the backend.");
      setTimeout(() => setFeedback(null), 2000);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-5 text-sm">
      {ACTIONS.map(({ type, label }) => (
        <button
          key={type}
          onClick={() => act(type)}
          disabled={busy !== null}
          className={`flex items-center gap-1.5 font-medium transition hover:text-signature disabled:opacity-50 ${
            type === "save" && saved ? "text-signature" : "text-ink-soft"
          }`}
        >
          {type === "save" && <IconBookmark className="h-3.5 w-3.5" filled={saved} />}
          {label}
        </button>
      ))}
      {feedback && <span className="text-xs text-ink-faint">{feedback}</span>}
    </div>
  );
}
