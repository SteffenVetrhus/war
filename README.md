# WARZONE MONITOR

A dystopian-themed web application that visualizes bombing incidents from the Iran conflict on an interactive dark map. Real-time news scraping meets dark cartographic visualization.

## Architecture

```
Browser (SvelteKit + Leaflet + Tailwind CSS v4)
    |
    | REST API (JSON over HTTP)
    |
FastAPI Backend (Python)
    |-- scraper.py  (BeautifulSoup4 + httpx)
    |-- geocoder.py (geopy + Nominatim)
    |-- models.py   (Pydantic v2)
    |-- config.py   (news source URLs)
    |-- data/       (cached incidents JSON)
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. The Vite dev server proxies `/api/*` requests to the backend.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/incidents` | List all bombing incidents |
| GET | `/api/incidents/{id}` | Get a single incident |
| GET | `/api/stats` | Aggregated statistics |
| POST | `/api/scrape` | Trigger manual news scrape |

## News Sources

- Al Jazeera
- Reuters
- BBC News
- AP News
- CNN

## Tech Stack

- **Frontend**: SvelteKit 2, Svelte 5, Tailwind CSS v4, Leaflet, TypeScript
- **Backend**: Python, FastAPI, BeautifulSoup4, httpx, geopy
- **Map Tiles**: CartoDB Dark Matter (free, no API key)
- **Geocoding**: OpenStreetMap Nominatim via geopy (free)
