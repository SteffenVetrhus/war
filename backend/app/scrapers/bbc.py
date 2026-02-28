"""BBC News scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper


class BBCScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "bbc"

    @property
    def name(self) -> str:
        return "BBC News"

    @property
    def description(self) -> str:
        return "BBC News Middle East — RSS feed + HTML fallback"

    FEED_URL = "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"
    PAGE_URL = "https://www.bbc.com/news/topics/cwlw3xz047jt"
    BASE_URL = "https://www.bbc.com"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        incidents = await self.scrape_feed(client, self.FEED_URL)
        if incidents:
            return incidents
        return await self.scrape_html(client, self.PAGE_URL, self.BASE_URL)
