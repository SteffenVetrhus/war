"""CNN scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class CNNScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "cnn"

    @property
    def name(self) -> str:
        return "CNN"

    @property
    def description(self) -> str:
        return "CNN Middle East — RSS feed + HTML fallback"

    FEED_URL = "http://rss.cnn.com/rss/edition_meast.rss"
    PAGE_URL = "https://edition.cnn.com/middleeast"
    BASE_URL = "https://edition.cnn.com"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        incidents = await self.scrape_feed(client, self.FEED_URL)
        if incidents:
            return incidents
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
