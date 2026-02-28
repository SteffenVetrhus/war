"""Al Jazeera scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class AlJazeeraScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "aljazeera"

    @property
    def name(self) -> str:
        return "Al Jazeera"

    @property
    def description(self) -> str:
        return "Al Jazeera English — RSS feed + HTML fallback"

    FEED_URL = "https://www.aljazeera.com/xml/rss/all.xml"
    PAGE_URL = "https://www.aljazeera.com/where/iran/"
    BASE_URL = "https://www.aljazeera.com"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        incidents = await self.scrape_feed(client, self.FEED_URL)
        if incidents:
            return incidents
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
