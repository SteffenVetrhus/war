import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import BombingIncident, StatsResponse, ScrapeResponse
from app.scraper import scrape_all_sources
from app.config import SCRAPE_INTERVAL_SECONDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
INCIDENTS_FILE = DATA_DIR / "incidents.json"

# In-memory store
incidents_store: list[BombingIncident] = []
last_updated: str | None = None
scrape_task: asyncio.Task | None = None


def _load_incidents() -> list[BombingIncident]:
    """Load incidents from JSON file."""
    if INCIDENTS_FILE.exists():
        try:
            data = json.loads(INCIDENTS_FILE.read_text())
            return [BombingIncident(**item) for item in data]
        except Exception as e:
            logger.error(f"Failed to load incidents: {e}")
    return []


def _save_incidents(items: list[BombingIncident]) -> None:
    """Save incidents to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = [item.model_dump() for item in items]
    INCIDENTS_FILE.write_text(json.dumps(data, indent=2))


def _merge_incidents(new_incidents: list[BombingIncident]) -> int:
    """Merge new incidents into the store, deduplicating by title. Returns count added."""
    existing_titles = {i.title.lower().strip() for i in incidents_store}
    added = 0
    for incident in new_incidents:
        if incident.title.lower().strip() not in existing_titles:
            incidents_store.append(incident)
            existing_titles.add(incident.title.lower().strip())
            added += 1
    if added > 0:
        _save_incidents(incidents_store)
    return added


async def _scheduled_scrape():
    """Background task that scrapes on a schedule."""
    global last_updated
    while True:
        try:
            logger.info("Starting scheduled scrape...")
            new_incidents = await scrape_all_sources()
            if new_incidents:
                added = _merge_incidents(new_incidents)
                if added > 0:
                    logger.info(f"Added {added} new incidents (total: {len(incidents_store)})")
            last_updated = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            logger.error(f"Scheduled scrape failed: {e}")

        await asyncio.sleep(SCRAPE_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global incidents_store, last_updated, scrape_task

    # Load cached data on startup
    incidents_store = _load_incidents()
    last_updated = datetime.now(timezone.utc).isoformat()
    logger.info(f"Loaded {len(incidents_store)} cached incidents")

    # Start background scraper
    scrape_task = asyncio.create_task(_scheduled_scrape())

    yield

    # Cleanup
    if scrape_task:
        scrape_task.cancel()
        try:
            await scrape_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Warzone Monitor API",
    description="API for tracking bombing incidents from news sources",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/incidents", response_model=list[BombingIncident])
async def get_incidents():
    """Return all tracked bombing incidents."""
    return incidents_store


@app.get("/api/incidents/{incident_id}", response_model=BombingIncident)
async def get_incident(incident_id: str):
    """Return a single incident by ID."""
    for incident in incidents_store:
        if incident.id == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Return aggregated statistics."""
    sources = set(i.source for i in incidents_store)
    return StatsResponse(
        total_incidents=len(incidents_store),
        total_killed=sum(i.killed for i in incidents_store),
        total_wounded=sum(i.wounded for i in incidents_store),
        sources_count=len(sources),
        last_updated=last_updated,
    )


@app.post("/api/scrape", response_model=ScrapeResponse)
async def trigger_scrape():
    """Manually trigger a news scrape."""
    global last_updated
    try:
        new_incidents = await scrape_all_sources()
        added = _merge_incidents(new_incidents)
        last_updated = datetime.now(timezone.utc).isoformat()
        return ScrapeResponse(
            status="success",
            new_incidents=added,
            message=f"Scrape completed. {added} new incidents added.",
        )
    except Exception as e:
        return ScrapeResponse(
            status="error",
            new_incidents=0,
            message=f"Scrape failed: {str(e)}",
        )
