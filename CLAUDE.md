# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A news monitoring webapp that scrapes Trump-Iran related articles from NYT, BBC, and CNBC every 10 minutes, displaying them with images in an A4-formatted layout.

## Build & Run Commands

```bash
# Full stack (backend + frontend + nginx)
docker-compose up --build

# Backend only (for development)
cd source/backend && pip install -r requirements.txt && python app.py

# Frontend only (for development)
cd source/frontend && npm install && npm start

# Run scraper manually
cd source/backend && python scraper.py
```

Access at `http://localhost:32000` (Docker) or `http://localhost:32000:3000` (frontend dev).

## Architecture

Three Docker services behind an Nginx reverse proxy:

- **Backend** (`source/backend/`, Flask on port 5000): `scraper.py` fetches articles from RSS feeds, filters for Trump/Iran keywords, saves to `data/articles.json`. `app.py` serves the JSON via REST API and runs APScheduler for 10-min intervals.
- **Frontend** (`source/frontend/`, React on port 3000): Fetches `/api/articles`, groups by source, renders ArticleCard components in A4 layout. Auto-polls every 10 minutes.
- **Nginx** (`source/nginx/`, port 31000→80): Routes `/api/*` → backend, `/*` → frontend.

## Key API Endpoints

- `GET /api/articles` — all scraped articles with metadata
- `GET /api/articles/<id>` — single article by MD5-based ID
- `GET /api/health` — health check

## Data Flow

Scraper → `data/articles.json` (shared via Docker volume) → Flask reads and serves → React fetches and displays.
