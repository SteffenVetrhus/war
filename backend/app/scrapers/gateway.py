"""Scraper Gateway — orchestrates all individual scraper services."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)


class ScraperGateway:
    """Central gateway that manages and orchestrates scraper services.

    Each scraper can be independently enabled or disabled at runtime.
    The gateway fans out requests to all enabled scrapers in parallel
    and deduplicates results.
    """

    def __init__(self, scrapers: list[BaseScraper]) -> None:
        self._scrapers: dict[str, BaseScraper] = {s.id: s for s in scrapers}
        self._enabled: dict[str, bool] = {s.id: True for s in scrapers}

    # ------------------------------------------------------------------
    # Integration registry
    # ------------------------------------------------------------------

    def list_integrations(self) -> list[dict]:
        """Return metadata for all registered scrapers + their enabled state."""
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "enabled": self._enabled[s.id],
            }
            for s in self._scrapers.values()
        ]

    def set_enabled(self, scraper_id: str, enabled: bool) -> bool:
        """Toggle a scraper on or off. Returns False if scraper_id unknown."""
        if scraper_id not in self._scrapers:
            return False
        self._enabled[scraper_id] = enabled
        logger.info(f"Scraper '{scraper_id}' {'enabled' if enabled else 'disabled'}")
        return True

    def is_enabled(self, scraper_id: str) -> bool | None:
        """Return the enabled state or None if unknown."""
        return self._enabled.get(scraper_id)

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    async def scrape_all(self) -> list[BombingIncident]:
        """Run all *enabled* scrapers in parallel and return deduplicated incidents."""
        active = [s for sid, s in self._scrapers.items() if self._enabled.get(sid)]
        if not active:
            logger.warning("No scrapers enabled — nothing to scrape")
            return []

        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            tasks = [s.scrape(client) for s in active]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        incidents: list[BombingIncident] = []
        seen_titles: set[str] = set()

        for result in results:
            if isinstance(result, list):
                for incident in result:
                    title_key = incident.title.lower().strip()
                    if title_key not in seen_titles:
                        incidents.append(incident)
                        seen_titles.add(title_key)
            elif isinstance(result, Exception):
                logger.warning(f"Scraper failed: {result}")

        logger.info(f"Gateway: {len(incidents)} total incidents from {len(active)} active scrapers")
        return incidents

    async def scrape_one(self, scraper_id: str) -> list[BombingIncident]:
        """Run a single scraper by ID (ignores enabled state)."""
        scraper = self._scrapers.get(scraper_id)
        if not scraper:
            return []

        async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            try:
                return await scraper.scrape(client)
            except Exception as e:
                logger.warning(f"Scraper '{scraper_id}' failed: {e}")
                return []
