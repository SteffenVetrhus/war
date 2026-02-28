"""Base class for all news scraper services."""

from __future__ import annotations

import re
import html
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.config import CONFLICT_KEYWORDS, IRAN_KEYWORDS
from app.models import BombingIncident
from app.geocoder import get_coordinates, KNOWN_LOCATIONS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# --- Casualty extraction patterns ---
CASUALTY_PATTERNS = [
    re.compile(r"(\d+)\s*(?:people\s+)?(?:were\s+)?(?:killed|dead|died|slain)", re.I),
    re.compile(r"(?:killed|dead|died|slain)\s+(\d+)", re.I),
    re.compile(r"(?:at\s+least\s+)(\d+)\s*(?:people\s+)?(?:killed|dead|died)", re.I),
    re.compile(r"death\s+toll[^.]*?(\d+)", re.I),
    re.compile(r"(\d+)\s*(?:casualties|fatalities)", re.I),
    re.compile(r"killing\s+(?:at\s+least\s+)?(\d+)", re.I),
    re.compile(r"(\d+)\s+deaths?\b", re.I),
    re.compile(r"claimed\s+(?:the\s+)?(?:lives?\s+of\s+)?(\d+)", re.I),
    re.compile(r"left\s+(?:at\s+least\s+)?(\d+)\s*(?:people\s+)?dead", re.I),
    re.compile(r"(\d+)\s*(?:people\s+)?(?:lost\s+their\s+lives|perished)", re.I),
    re.compile(r"(\d+)\s*(?:people\s+)?confirmed\s+dead", re.I),
    re.compile(r"(?:toll|count)\s+(?:has\s+)?(?:risen?\s+to|reached?)\s+(\d+)", re.I),
]

WOUNDED_PATTERNS = [
    re.compile(r"(\d+)\s*(?:people\s+)?(?:were\s+)?(?:wounded|injured|hurt)", re.I),
    re.compile(r"(?:wounded|injured|hurt)\s+(\d+)", re.I),
    re.compile(r"(?:at\s+least\s+)(\d+)\s*(?:people\s+)?(?:wounded|injured)", re.I),
    re.compile(r"(?:wounding|injuring)\s+(?:at\s+least\s+)?(\d+)", re.I),
    re.compile(r"(\d+)\s*(?:people\s+)?(?:hospitalized|taken\s+to\s+hospital)", re.I),
    re.compile(r"(\d+)\s*(?:people\s+)?(?:treated\s+for)", re.I),
]

_ALL_KEYWORDS = CONFLICT_KEYWORDS + IRAN_KEYWORDS


class BaseScraper(ABC):
    """Abstract base class for a standalone news scraper service."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique machine-readable identifier (e.g. 'aljazeera')."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name (e.g. 'Al Jazeera')."""

    @property
    def description(self) -> str:
        return f"Scraper for {self.name}"

    @abstractmethod
    async def scrape(self, client: httpx.AsyncClient) -> list[BombingIncident]:
        """Run the scraper and return discovered incidents."""

    # ------------------------------------------------------------------
    # Shared helpers available to all sub-scrapers
    # ------------------------------------------------------------------

    @staticmethod
    def is_relevant(text: str, title: str = "") -> bool:
        combined = f"{title} {text}".lower()
        has_conflict = any(kw in combined for kw in CONFLICT_KEYWORDS)
        has_iran = any(kw in combined for kw in IRAN_KEYWORDS)
        return has_conflict and has_iran

    @staticmethod
    def extract_killed(text: str) -> int:
        return _extract_count(text, CASUALTY_PATTERNS, 10_000)

    @staticmethod
    def extract_wounded(text: str) -> int:
        return _extract_count(text, WOUNDED_PATTERNS, 50_000)

    @staticmethod
    def extract_location(text: str) -> str | None:
        text_lower = text.lower()
        sorted_locations = sorted(KNOWN_LOCATIONS.keys(), key=len, reverse=True)
        for location in sorted_locations:
            if location in text_lower:
                return location.title()

        location_re = re.compile(
            r"(?:in|near|outside|targeting|struck|hit|toward|towards|on)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        )
        for match in location_re.findall(text):
            coords = get_coordinates(match)
            if coords:
                return match
        return None

    @staticmethod
    def parse_date(date_str: str) -> str:
        if not date_str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if len(date_str) >= 10 and re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str[:10]
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def parse_rss_entries(xml_text: str) -> list[dict]:
        entries: list[dict] = []

        items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
        for item_xml in items:
            title_m = re.search(r"<title[^>]*>(.*?)</title>", item_xml, re.DOTALL)
            link_m = re.search(r"<link[^>]*>\s*(.*?)\s*</link>", item_xml, re.DOTALL)
            if not link_m or not link_m.group(1).strip():
                link_m = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', item_xml)
            desc_m = re.search(r"<description[^>]*>(.*?)</description>", item_xml, re.DOTALL)
            date_m = re.search(r"<pubDate[^>]*>(.*?)</pubDate>", item_xml, re.DOTALL)
            source_m = re.search(r'<source[^>]*url=["\']([^"\']*)["\'][^>]*>(.*?)</source>', item_xml, re.DOTALL)

            raw_title = title_m.group(1).strip() if title_m else ""
            if not raw_title:
                continue

            def _clean_cdata(s: str) -> str:
                return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.DOTALL).strip()

            title = _clean_cdata(raw_title)
            link = _clean_cdata(link_m.group(1).strip()) if link_m else ""
            desc = _clean_cdata(desc_m.group(1).strip()) if desc_m else ""
            desc = re.sub(r"<[^>]+>", " ", desc)
            desc = html.unescape(desc).strip()
            desc = re.sub(r"\s+", " ", desc)

            date = date_m.group(1).strip() if date_m else ""

            entries.append({
                "title": html.unescape(title),
                "link": link,
                "summary": desc,
                "date": date,
                "source": source_m.group(2).strip() if source_m else "",
                "source_url": source_m.group(1).strip() if source_m else "",
            })

        if not entries:
            atom_entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)
            for entry_xml in atom_entries:
                title_m = re.search(r"<title[^>]*>(.*?)</title>", entry_xml, re.DOTALL)
                link_m = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', entry_xml)
                summary_m = re.search(r"<(?:summary|content)[^>]*>(.*?)</(?:summary|content)>", entry_xml, re.DOTALL)
                date_m = re.search(r"<(?:published|updated)[^>]*>(.*?)</(?:published|updated)>", entry_xml, re.DOTALL)

                raw_title = title_m.group(1).strip() if title_m else ""
                if not raw_title:
                    continue

                entries.append({
                    "title": html.unescape(re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", raw_title, flags=re.DOTALL)),
                    "link": link_m.group(1) if link_m else "",
                    "summary": re.sub(r"<[^>]+>", " ", summary_m.group(1)).strip() if summary_m else "",
                    "date": date_m.group(1).strip() if date_m else "",
                    "source": "",
                    "source_url": "",
                })

        return entries

    def incident_from_feed_entry(self, entry: dict, source_name: str | None = None) -> BombingIncident | None:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = f"{title}. {summary}"

        if not self.is_relevant(summary, title):
            return None

        location = self.extract_location(title) or self.extract_location(summary)
        if not location:
            return None

        coords = get_coordinates(location)
        if not coords:
            return None

        killed = self.extract_killed(combined)
        wounded = self.extract_wounded(combined)
        date_str = self.parse_date(entry.get("date", ""))

        entry_source = entry.get("source") or source_name or self.name
        source_url = entry.get("source_url") or entry.get("link", "")

        description = summary[:300].strip()
        if len(summary) > 300:
            description += "..."

        return BombingIncident(
            id=str(uuid.uuid4()),
            title=title,
            location=location,
            latitude=coords[0],
            longitude=coords[1],
            date=date_str,
            killed=killed,
            wounded=wounded,
            description=description,
            source=entry_source,
            source_url=source_url,
        )

    def parse_article(self, html_text: str, url: str) -> BombingIncident | None:
        soup = BeautifulSoup(html_text, "lxml")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None

        article_tag = (
            soup.find("article")
            or soup.find("div", class_=re.compile(r"article|story|content|body|post"))
            or soup.find("main")
        )
        if article_tag:
            paragraphs = article_tag.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        if not text or not self.is_relevant(text, title):
            return None

        location = self.extract_location(title) or self.extract_location(text)
        if not location:
            return None

        coords = get_coordinates(location)
        if not coords:
            return None

        killed = self.extract_killed(text)
        wounded = self.extract_wounded(text)

        time_tag = soup.find("time")
        date_str = ""
        if time_tag and time_tag.get("datetime"):
            date_str = time_tag["datetime"][:10]
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        description = text[:300].strip()
        if len(text) > 300:
            description += "..."

        return BombingIncident(
            id=str(uuid.uuid4()),
            title=title,
            location=location,
            latitude=coords[0],
            longitude=coords[1],
            date=date_str,
            killed=killed,
            wounded=wounded,
            description=description,
            source=self.name,
            source_url=url,
        )

    def extract_article_links(self, html_text: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html_text, "lxml")
        links: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True).lower()

            has_keyword = any(kw in text for kw in _ALL_KEYWORDS)
            if not has_keyword:
                parent_text = a_tag.parent.get_text(strip=True).lower() if a_tag.parent else ""
                has_keyword = any(kw in parent_text for kw in _ALL_KEYWORDS)
            if not has_keyword:
                href_lower = href.lower()
                has_keyword = any(kw.replace(" ", "-") in href_lower for kw in _ALL_KEYWORDS)

            if has_keyword:
                if href.startswith("/"):
                    href = base_url.rstrip("/") + href
                elif not href.startswith("http"):
                    continue
                links.add(href)

        return list(links)[:20]

    async def scrape_feed(self, client: httpx.AsyncClient, feed_url: str) -> list[BombingIncident]:
        incidents: list[BombingIncident] = []
        try:
            resp = await client.get(feed_url)
            resp.raise_for_status()

            entries = self.parse_rss_entries(resp.text)
            logger.info(f"[{self.id}] Parsed {len(entries)} entries from feed")

            relevant = [e for e in entries if self.is_relevant(e.get("summary", ""), e.get("title", ""))]
            logger.info(f"[{self.id}] {len(relevant)} relevant entries")

            for entry in relevant:
                incident = self.incident_from_feed_entry(entry)

                if entry.get("link"):
                    try:
                        art_resp = await client.get(entry["link"], follow_redirects=True)
                        if art_resp.status_code == 200:
                            full_incident = self.parse_article(art_resp.text, entry["link"])
                            if full_incident:
                                incident = full_incident
                    except Exception:
                        pass

                if incident:
                    incidents.append(incident)
                    logger.info(f"[{self.id}] Feed incident: {incident.title[:60]} (killed={incident.killed})")

        except Exception as e:
            logger.warning(f"[{self.id}] Failed to scrape feed: {e}")

        return incidents

    async def scrape_html(self, client: httpx.AsyncClient, url: str, base_url: str) -> list[BombingIncident]:
        incidents: list[BombingIncident] = []
        try:
            logger.info(f"[{self.id}] Scraping HTML from {url}...")
            resp = await client.get(url)
            resp.raise_for_status()

            article_links = self.extract_article_links(resp.text, base_url)
            logger.info(f"[{self.id}] Found {len(article_links)} potential articles")

            for link in article_links:
                try:
                    art_resp = await client.get(link)
                    art_resp.raise_for_status()
                    incident = self.parse_article(art_resp.text, link)
                    if incident:
                        incidents.append(incident)
                        logger.info(f"[{self.id}] Extracted: {incident.title[:60]}")
                except Exception as e:
                    logger.debug(f"[{self.id}] Failed to parse {link}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"[{self.id}] Failed HTML scrape: {e}")

        return incidents


def _extract_count(text: str, patterns: list[re.Pattern], max_threshold: int) -> int:
    result = 0
    for pattern in patterns:
        for match in pattern.findall(text):
            try:
                num = int(match)
                if num < max_threshold:
                    result = max(result, num)
            except ValueError:
                pass
    return result
