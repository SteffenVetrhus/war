import re
import html
import uuid
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.config import NEWS_SOURCES, GOOGLE_NEWS_FEEDS, CONFLICT_KEYWORDS, IRAN_KEYWORDS
from app.models import BombingIncident
from app.geocoder import get_coordinates, KNOWN_LOCATIONS

logger = logging.getLogger(__name__)

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _is_relevant(text: str, title: str = "") -> bool:
    """Check if article text is relevant to Iran conflict."""
    combined = f"{title} {text}".lower()
    has_conflict = any(kw in combined for kw in CONFLICT_KEYWORDS)
    has_iran = any(kw in combined for kw in IRAN_KEYWORDS)
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
    """Extract the most likely location from text."""
    text_lower = text.lower()
    # Check known locations — longest first so "bandar abbas" matches before "ban..."
    sorted_locations = sorted(KNOWN_LOCATIONS.keys(), key=len, reverse=True)
    for location in sorted_locations:
        if location in text_lower:
            return location.title()

    # Try regex patterns for "in <City>", "near <City>", "struck <City>"
    location_re = re.compile(
        r"(?:in|near|outside|targeting|struck|hit|toward|towards|on)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    )
    for match in location_re.findall(text):
        coords = get_coordinates(match)
        if coords:
            return match

    return None


_ALL_KEYWORDS = CONFLICT_KEYWORDS + IRAN_KEYWORDS


# ---------------------------------------------------------------------------
# RSS / Atom feed parsing
# ---------------------------------------------------------------------------

def _parse_rss_entries(xml_text: str) -> list[dict]:
    """Parse RSS/Atom feed entries using regex for maximum reliability."""
    entries: list[dict] = []

    # RSS <item> blocks
    items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    for item_xml in items:
        title_m = re.search(r"<title[^>]*>(.*?)</title>", item_xml, re.DOTALL)
        link_m = re.search(r"<link[^>]*>\s*(.*?)\s*</link>", item_xml, re.DOTALL)
        # Some feeds have link as self-closing with href
        if not link_m or not link_m.group(1).strip():
            link_m = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', item_xml)
        desc_m = re.search(r"<description[^>]*>(.*?)</description>", item_xml, re.DOTALL)
        date_m = re.search(r"<pubDate[^>]*>(.*?)</pubDate>", item_xml, re.DOTALL)
        source_m = re.search(r'<source[^>]*url=["\']([^"\']*)["\'][^>]*>(.*?)</source>', item_xml, re.DOTALL)

        raw_title = title_m.group(1).strip() if title_m else ""
        if not raw_title:
            continue

        # Clean CDATA wrappers
        def _clean_cdata(s: str) -> str:
            return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.DOTALL).strip()

        title = _clean_cdata(raw_title)
        link = _clean_cdata(link_m.group(1).strip()) if link_m else ""
        desc = _clean_cdata(desc_m.group(1).strip()) if desc_m else ""
        # Strip HTML tags from description and decode entities
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

    # Atom <entry> fallback
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


def _parse_date(date_str: str) -> str:
    """Try to parse various date formats into YYYY-MM-DD."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Already ISO
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


# ---------------------------------------------------------------------------
# Article link extraction (HTML scraping fallback)
# ---------------------------------------------------------------------------

def _extract_article_links(html_text: str, base_url: str) -> list[str]:
    """Extract article links from a news listing page."""
    soup = BeautifulSoup(html_text, "lxml")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()

        # Check link text, parent text, and URL path for any keyword
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


# ---------------------------------------------------------------------------
# Article parsing
# ---------------------------------------------------------------------------

def _parse_article(html_text: str, url: str, source_name: str) -> BombingIncident | None:
    """Parse a single article page into a BombingIncident."""
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
    if not text or not _is_relevant(text, title):
        return None

    location = _extract_location(title) or _extract_location(text)
    if not location:
        return None

    coords = get_coordinates(location)
    if not coords:
        return None

    killed = _extract_killed(text)
    wounded = _extract_wounded(text)

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
        source=source_name,
        source_url=url,
    )


# ---------------------------------------------------------------------------
# Feed-based incident extraction
# ---------------------------------------------------------------------------

def _incident_from_feed_entry(entry: dict, source_name: str) -> BombingIncident | None:
    """Create a BombingIncident from an RSS feed entry (title + summary)."""
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    combined = f"{title}. {summary}"

    if not _is_relevant(summary, title):
        return None

    location = _extract_location(title) or _extract_location(summary)
    if not location:
        return None

    coords = get_coordinates(location)
    if not coords:
        return None

    killed = _extract_killed(combined)
    wounded = _extract_wounded(combined)
    date_str = _parse_date(entry.get("date", ""))

    entry_source = entry.get("source") or source_name
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


# ---------------------------------------------------------------------------
# Source scraping — feeds and HTML
# ---------------------------------------------------------------------------

async def _scrape_feed(client: httpx.AsyncClient, feed_url: str, source_name: str) -> list[BombingIncident]:
    """Scrape incidents from an RSS/Atom feed."""
    incidents: list[BombingIncident] = []
    try:
        resp = await client.get(feed_url)
        resp.raise_for_status()

        entries = _parse_rss_entries(resp.text)
        logger.info(f"Parsed {len(entries)} entries from {source_name} feed")

        relevant = [e for e in entries if _is_relevant(e.get("summary", ""), e.get("title", ""))]
        logger.info(f"  {len(relevant)} relevant entries from {source_name} feed")

        for entry in relevant:
            # Build incident from feed entry first
            incident = _incident_from_feed_entry(entry, source_name)

            # Try fetching full article for richer extraction
            if entry.get("link"):
                try:
                    art_resp = await client.get(entry["link"], follow_redirects=True)
                    if art_resp.status_code == 200:
                        full_incident = _parse_article(art_resp.text, entry["link"], source_name)
                        if full_incident:
                            incident = full_incident
                except Exception:
                    pass  # Keep the feed-based incident

            if incident:
                incidents.append(incident)
                logger.info(f"  Feed incident: {incident.title[:60]} (killed={incident.killed})")

    except Exception as e:
        logger.warning(f"Failed to scrape feed {source_name}: {e}")

    return incidents


async def _scrape_source(client: httpx.AsyncClient, source: dict) -> list[BombingIncident]:
    """Scrape a single news source for bombing incidents."""
    incidents: list[BombingIncident] = []

    # Try RSS feed first (much more reliable than HTML scraping)
    if source.get("feed_url"):
        feed_incidents = await _scrape_feed(client, source["feed_url"], source["name"])
        if feed_incidents:
            return feed_incidents

    # Fall back to HTML scraping
    try:
        logger.info(f"Scraping {source['name']} (HTML)...")
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


async def _scrape_google_news(client: httpx.AsyncClient) -> list[BombingIncident]:
    """Scrape incidents from Google News RSS search feeds."""
    all_incidents: list[BombingIncident] = []
    for feed_url in GOOGLE_NEWS_FEEDS:
        incidents = await _scrape_feed(client, feed_url, "Google News")
        all_incidents.extend(incidents)
    return all_incidents


async def scrape_all_sources() -> list[BombingIncident]:
    """Scrape all configured news sources for bombing incidents in parallel."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
        tasks = [_scrape_source(client, source) for source in NEWS_SOURCES]
        tasks.append(_scrape_google_news(client))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    incidents: list[BombingIncident] = []
    seen_titles: set[str] = set()

    for result in results:
        if isinstance(result, list):
            for incident in result:
                # Deduplicate by normalized title within this scrape run
                title_key = incident.title.lower().strip()
                if title_key not in seen_titles:
                    incidents.append(incident)
                    seen_titles.add(title_key)
        elif isinstance(result, Exception):
            logger.warning(f"Source scrape failed: {result}")

    logger.info(f"Total incidents scraped: {len(incidents)}")
    return incidents
