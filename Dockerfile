# One container serves both the React frontend and the FastAPI backend.

# ── Stage 1: build the React frontend ────────────────────────────────────────
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend + the built frontend ─────────────────────────────
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SERVE_FRONTEND=true
WORKDIR /app

COPY requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY backend/ ./backend/
COPY data/mock_articles.json ./data/mock_articles.json
COPY --from=frontend /frontend/dist ./frontend/dist

# Hosting platforms pass the port to listen on in $PORT.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
