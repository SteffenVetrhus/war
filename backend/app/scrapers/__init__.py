from app.scrapers.base import BaseScraper
from app.scrapers.aljazeera import AlJazeeraScraper
from app.scrapers.vg import VGScraper
from app.scrapers.bbc import BBCScraper
from app.scrapers.reuters import ReutersScraper
from app.scrapers.apnews import APNewsScraper
from app.scrapers.cnn import CNNScraper
from app.scrapers.google_news import GoogleNewsScraper

ALL_SCRAPERS: list[BaseScraper] = [
    AlJazeeraScraper(),
    VGScraper(),
    BBCScraper(),
    ReutersScraper(),
    APNewsScraper(),
    CNNScraper(),
    GoogleNewsScraper(),
]

__all__ = [
    "BaseScraper",
    "AlJazeeraScraper",
    "VGScraper",
    "BBCScraper",
    "ReutersScraper",
    "APNewsScraper",
    "CNNScraper",
    "GoogleNewsScraper",
    "ALL_SCRAPERS",
]
