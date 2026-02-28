"""AP News scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class APNewsScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "apnews"

    @property
    def name(self) -> str:
        return "AP News"

    @property
    def description(self) -> str:
        return "Associated Press — Iran hub, HTML scraping"

    PAGE_URL = "https://apnews.com/hub/iran"
    BASE_URL = "https://apnews.com"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
