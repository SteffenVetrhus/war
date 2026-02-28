# CLAUDE.md

## Project Overview

WARZONE MONITOR — a dystopian-themed web app that visualizes bombing incidents from the Iran conflict on an interactive dark map. Python FastAPI backend scrapes news sources; SvelteKit frontend renders incidents on a Leaflet map.

## Architecture

- **Backend**: Python 3.12 / FastAPI / BeautifulSoup4 / httpx / geopy — serves REST API on port 8000
- **Frontend**: SvelteKit 2 / Svelte 5 / Tailwind CSS v4 / Leaflet / TypeScript — dev server on port 5173
- **Data**: In-memory store with JSON file persistence (no database)
- **Map tiles**: CartoDB Dark Matter (free, no API key)
- **Geocoding**: Hardcoded Iranian locations with Nominatim fallback

## Build & Run

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

Frontend available at `http://localhost:5173`, backend API at `http://localhost:8000/docs`.

## Project Structure

```
backend/
  app/
    main.py       — FastAPI app, endpoints, lifespan, CORS
    scraper.py    — News scraping logic (httpx + BeautifulSoup4)
    geocoder.py   — Location → coordinates (hardcoded + Nominatim)
    models.py     — Pydantic v2 data models
    config.py     — News source URLs, keywords
  data/           — Cached incidents JSON
  requirements.txt
  run.py          — Entry point (uvicorn)

frontend/
  src/
    routes/       — SvelteKit pages (+page.svelte, +layout.svelte)
    lib/
      components/ — Header, Map, Sidebar, IncidentCard (.svelte)
      stores/     — Svelte 5 reactive stores (bombings.svelte.ts)
      types/      — TypeScript interfaces
    app.css       — Global styles, animations, dystopian theme
    app.html      — HTML shell
  vite.config.ts  — Vite + SvelteKit + Tailwind plugins, API proxy
  svelte.config.js
  package.json
```

## API Endpoints

- `GET /api/incidents` — list all bombing incidents
- `GET /api/incidents/{id}` — single incident
- `GET /api/stats` — aggregated statistics
- `POST /api/scrape` — trigger manual news scrape

## Code Conventions

- Backend uses Pydantic v2 models for all request/response schemas
- Frontend uses Svelte 5 runes (`$state`, `$derived`, `$effect`) — not legacy stores
- CSS uses Tailwind v4 with `@theme` custom properties (not tailwind.config.js)
- TypeScript strict mode enabled
- Client-side rendering only (SSR disabled)
- Async/await throughout (backend uses httpx async client, asyncio.gather for parallel scraping)
