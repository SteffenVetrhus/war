import re
import uuid
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.config import NEWS_SOURCES, CONFLICT_KEYWORDS, IRAN_KEYWORDS
from app.models import BombingIncident
from app.geocoder import get_coordinates, KNOWN_LOCATIONS

logger = logging.getLogger(__name__)

CASUALTY_PATTERNS = [
    re.compile(r"(\d+)\s*(?:people\s+)?(?:were\s+)?(?:killed|dead|died|slain)", re.IGNORECASE),
    re.compile(r"(?:killed|dead|died|slain)\s+(\d+)", re.IGNORECASE),
    re.compile(r"(?:at\s+least\s+)(\d+)\s*(?:people\s+)?(?:killed|dead|died)", re.IGNORECASE),
    re.compile(r"death\s+toll[^.]*?(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*(?:casualties|fatalities)", re.IGNORECASE),
]

WOUNDED_PATTERNS = [
    re.compile(r"(\d+)\s*(?:people\s+)?(?:were\s+)?(?:wounded|injured|hurt)", re.IGNORECASE),
    re.compile(r"(?:wounded|injured|hurt)\s+(\d+)", re.IGNORECASE),
    re.compile(r"(?:at\s+least\s+)(\d+)\s*(?:people\s+)?(?:wounded|injured)", re.IGNORECASE),
]

NOTABLE_FIGURE_PATTERNS = [
    re.compile(r"(?:commander|general|leader|official|minister|president|chief)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", re.IGNORECASE),
    re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(?:a\s+)?(?:senior|top|high-ranking|military|political)\s+(?:commander|general|leader|official)", re.IGNORECASE),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _is_relevant(text: str) -> bool:
    """Check if article text is relevant to Iran conflict."""
    text_lower = text.lower()
    has_conflict = any(kw in text_lower for kw in CONFLICT_KEYWORDS)
    has_iran = any(kw in text_lower for kw in IRAN_KEYWORDS)
    return has_conflict and has_iran


def _extract_count(text: str, patterns: list[re.Pattern], max_threshold: int) -> int:
    """Extract the highest matching number from text using the given regex patterns."""
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


def _extract_killed(text: str) -> int:
    return _extract_count(text, CASUALTY_PATTERNS, 10000)


def _extract_wounded(text: str) -> int:
    return _extract_count(text, WOUNDED_PATTERNS, 50000)


def _extract_location(text: str) -> str | None:
    """Extract the most likely Iranian location from text."""
    text_lower = text.lower()
    for location in KNOWN_LOCATIONS:
        if location in text_lower:
            return location.title()
    return None


def _extract_notable_figures(text: str) -> list[str]:
    """Extract names of notable figures mentioned."""
    figures = []
    for pattern in NOTABLE_FIGURE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            name = match.strip()
            if len(name) > 3 and name not in figures:
                figures.append(name)
    return figures[:5]  # limit to 5


_ALL_KEYWORDS = CONFLICT_KEYWORDS + IRAN_KEYWORDS


def _extract_article_links(html: str, base_url: str) -> list[str]:
    """Extract article links from a news listing page."""
    soup = BeautifulSoup(html, "lxml")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()

        # Check if link text or surrounding text contains relevant keywords
        has_keyword = any(kw in text for kw in _ALL_KEYWORDS)
        if not has_keyword:
            parent_text = a_tag.parent.get_text(strip=True).lower() if a_tag.parent else ""
            has_keyword = any(kw in parent_text for kw in IRAN_KEYWORDS)

        if has_keyword:
            if href.startswith("/"):
                href = base_url.rstrip("/") + href
            elif not href.startswith("http"):
                continue
            links.add(href)

    return list(links)[:20]  # limit per source


def _parse_article(html: str, url: str, source_name: str) -> BombingIncident | None:
    """Parse a single article page into a BombingIncident."""
    soup = BeautifulSoup(html, "lxml")

    # Extract title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""
    if not title:
        return None

    # Extract article body text
    article_tag = soup.find("article") or soup.find("div", class_=re.compile(r"article|story|content"))
    if article_tag:
        paragraphs = article_tag.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text = " ".join(p.get_text(strip=True) for p in paragraphs)
    if not text or not _is_relevant(text):
        return None

    # Extract data
    location = _extract_location(text) or _extract_location(title)
    if not location:
        return None

    coords = get_coordinates(location)
    if not coords:
        return None

    killed = _extract_killed(text)
    wounded = _extract_wounded(text)
    notable = _extract_notable_figures(text)

    # Extract date
    time_tag = soup.find("time")
    date_str = ""
    if time_tag and time_tag.get("datetime"):
        date_str = time_tag["datetime"][:10]
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build description (first 200 chars of article)
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
        notable_figures=notable,
        description=description,
        source=source_name,
        source_url=url,
    )


async def _scrape_source(client: httpx.AsyncClient, source: dict) -> list[BombingIncident]:
    """Scrape a single news source for bombing incidents."""
    incidents: list[BombingIncident] = []
    try:
        logger.info(f"Scraping {source['name']}...")
        resp = await client.get(source["url"])
        resp.raise_for_status()

        article_links = _extract_article_links(resp.text, source["base_url"])
        logger.info(f"Found {len(article_links)} potential articles from {source['name']}")

        for link in article_links:
            try:
                art_resp = await client.get(link)
                art_resp.raise_for_status()

                incident = _parse_article(art_resp.text, link, source["name"])
                if incident:
                    incidents.append(incident)
                    logger.info(f"  Extracted incident: {incident.title[:60]}")
            except Exception as e:
                logger.debug(f"  Failed to parse {link}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Failed to scrape {source['name']}: {e}")

    return incidents


async def scrape_all_sources() -> list[BombingIncident]:
    """Scrape all configured news sources for bombing incidents in parallel."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
        results = await asyncio.gather(
            *[_scrape_source(client, source) for source in NEWS_SOURCES],
            return_exceptions=True,
        )

    incidents: list[BombingIncident] = []
    for result in results:
        if isinstance(result, list):
            incidents.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Source scrape failed: {result}")

    logger.info(f"Total incidents scraped: {len(incidents)}")
    return incidents
