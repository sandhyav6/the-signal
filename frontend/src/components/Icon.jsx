// A handful of hand-drawn SVG icons — no icon library, no emoji.

export function IconChevron({ className = "" }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path d="M6 8l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconSearch({ className = "" }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.6" />
      <path d="M14 14l4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function IconBookmark({ className = "", filled = false }) {
  return (
    <svg viewBox="0 0 20 20" fill={filled ? "currentColor" : "none"} className={className} aria-hidden="true">
      <path
        d="M5.5 3.5h9a.5.5 0 01.5.5v13l-5-3.1-5 3.1V4a.5.5 0 01.5-.5z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}
