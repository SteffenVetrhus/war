"""VG (Verdens Gang) Norwegian news scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class VGScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "vg"

    @property
    def name(self) -> str:
        return "VG"

    @property
    def description(self) -> str:
        return "VG Nyheter — Norwegian news, HTML scraping"

    PAGE_URL = "https://www.vg.no/nyheter/utenriks/"
    BASE_URL = "https://www.vg.no"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
