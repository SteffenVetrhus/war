"""Google News aggregator scraper service."""

import httpx

from app.models import BombingIncident
from app.scrapers.base import BaseScraper

GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=Iran+strike+bombing+missile+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+airstrike+killed+casualties+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+war+attack+military+strike+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Tehran+Isfahan+missile+strike+when:7d&hl=en-US&gl=US&ceid=US:en",
]


class GoogleNewsScraper(BaseScraper):
    @property
    def id(self) -> str:
        return "google_news"

    @property
    def name(self) -> str:
        return "Google News"

    @property
    def description(self) -> str:
        return "Google News RSS search aggregator — multiple keyword feeds"

    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        all_incidents: list[BombingIncident] = []
        for feed_url in GOOGLE_NEWS_FEEDS:
            incidents = await self.scrape_feed(client, feed_url)
            all_incidents.extend(incidents)
        return all_incidents
