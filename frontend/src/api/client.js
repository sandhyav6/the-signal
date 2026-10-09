// API client — the app's only channel to the FastAPI backend.
// In dev, Vite proxies /api/* to http://127.0.0.1:8000 (see vite.config.js),
// so the browser never needs CORS. For a separately-hosted build, set
// VITE_API_BASE to the backend's full origin.
const BASE = import.meta.env.VITE_API_BASE || "/api";

// This project has no login flow — a single default user (id=1) is created
// by the seed script, matching backend/models/models.py's User docstring.
export const DEFAULT_USER_ID = 1;

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request(method, path, { params, body } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) url.searchParams.set(key, value);
    });
  }

  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.error || response.statusText, response.status, data?.code);
  }
  return data;
}

export const getCategories = () => request("GET", "/categories");

export const getArticles = (page = 1, limit = 20, category) =>
  request("GET", "/articles", { params: { page, limit, category } });

export const getArticle = (articleId) => request("GET", `/articles/${articleId}`);

export const getFeed = (userId, type = "foryou", category, page = 1) =>
  request("GET", "/feed", { params: { user_id: userId, type, category, page } });

export const search = (query, page = 1) => request("GET", "/search", { params: { q: query, page } });

export const suggest = (prefix) => request("GET", "/search/suggest", { params: { prefix } });

export const getTrending = (limit = 5) => request("GET", "/trending", { params: { limit } });

export const postInteraction = (userId, articleId, type) =>
  request("POST", "/interactions", { body: { user_id: userId, article_id: articleId, type } });

export const postBookmark = (userId, articleId) =>
  request("POST", "/bookmarks", { body: { user_id: userId, article_id: articleId } });

export const getBookmarks = (userId) => request("GET", "/bookmarks", { params: { user_id: userId } });

export const getHistory = (userId) => request("GET", "/history", { params: { user_id: userId } });

export const getPreferences = (userId) => request("GET", "/preferences", { params: { user_id: userId } });

export const putPreferences = (userId, updates) =>
  request("PUT", "/preferences", { body: { user_id: userId, updates } });

export const postRefresh = (mode) => request("POST", "/refresh", { body: mode ? { mode } : {} });

export const getStatus = () => request("GET", "/status");
