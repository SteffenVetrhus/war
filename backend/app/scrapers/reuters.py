"""Reuters scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class ReutersScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "reuters"

    @property
    def name(self) -> str:
        return "Reuters"

    @property
    def description(self) -> str:
        return "Reuters World/Middle East — HTML scraping"

    PAGE_URL = "https://www.reuters.com/world/middle-east/"
    BASE_URL = "https://www.reuters.com"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
