#!/usr/bin/env python3
"""
Scrape the Victorian Labor "News" page and generate an RSS 2.0 feed.

The site (viclabor.org.au) is built on Webflow with a CMS "collection list"
of news items. There's no built-in RSS feed, so this script re-derives one
by:
  1. Finding every link that points at an individual article
     (https://www.viclabor.org.au/news/<slug>)
  2. Picking the most sensible title text for each (the longest piece of
     link/heading text associated with that URL, since Webflow often wraps
     a short category badge AND the headline in separate elements pointing
     at the same href)
  3. Looking for a "DD Month YYYY" style date near each item and parsing it
  4. Writing the result out as feed.xml (RSS 2.0)

This is intentionally defensive/heuristic rather than tied to exact CSS
class names, because Webflow regenerates class names and this page's
markup wasn't available to hand-verify while writing this script. If the
titles or dates come out wrong after the first real run, the fix is almost
always a small tweak to `extract_items()` below.
"""

import datetime as dt
import hashlib
import re
import sys
from email.utils import format_datetime
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

SITE = "https://www.viclabor.org.au"
NEWS_URL = f"{SITE}/news"
FEED_PATH = "feed.xml"
MAX_ITEMS = 30

ARTICLE_HREF_RE = re.compile(r"^/news/[a-z0-9][a-z0-9-]*/?$", re.IGNORECASE)
DATE_RE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{4})\b",
    re.IGNORECASE,
)


def fetch_html(url: str) -> str:
    resp = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; ViclaborNewsFeedBot/1.0; "
                "+https://github.com/) RSS generator for personal use"
            )
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_date(text: str):
    m = DATE_RE.search(text)
    if not m:
        return None
    day, month_name, year = m.groups()
    try:
        return dt.datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError:
        return None


def find_card(anchor):
    """Climb up from an <a> tag to find its containing "card" element,
    i.e. the smallest ancestor whose text also contains a date. Falls back
    to a fixed number of levels up if no date is found nearby."""
    node = anchor
    for _ in range(6):
        if node.parent is None:
            break
        node = node.parent
        text = node.get_text(" ", strip=True)
        if DATE_RE.search(text):
            return node
    # Fallback: just go up 3 levels from the anchor
    node = anchor
    for _ in range(3):
        if node.parent is None:
            break
        node = node.parent
    return node


def extract_items(html: str):
    soup = BeautifulSoup(html, "html.parser")

    anchors = [
        a
        for a in soup.find_all("a", href=True)
        if ARTICLE_HREF_RE.match(a["href"].split("?")[0].split("#")[0])
    ]

    # Group anchors by the article URL they point to, preserving first-seen order.
    by_href = {}
    order = []
    for a in anchors:
        href = a["href"].split("?")[0].split("#")[0].rstrip("/")
        if href not in by_href:
            by_href[href] = []
            order.append(href)
        by_href[href].append(a)

    items = []
    for href in order:
        link = urljoin(SITE + "/", href.lstrip("/"))
        candidate_anchors = by_href[href]

        # Prefer a heading tag's text if one of the anchors wraps/contains one.
        title = None
        for a in candidate_anchors:
            heading = a.find(re.compile("^h[1-6]$"))
            if heading and heading.get_text(strip=True):
                title = heading.get_text(" ", strip=True)
                break

        # Otherwise use the longest anchor text (headline is usually longer
        # than a short category badge like "Media Release").
        if not title:
            texts = [a.get_text(" ", strip=True) for a in candidate_anchors]
            texts = [t for t in texts if t]
            if texts:
                title = max(texts, key=len)

        if not title:
            # Last resort: derive a readable title from the URL slug.
            slug = href.rsplit("/", 1)[-1]
            title = slug.replace("-", " ").title()

        card = find_card(candidate_anchors[0])
        card_text = card.get_text(" ", strip=True)
        pub_date = parse_date(card_text)

        items.append(
            {
                "title": title.strip(),
                "link": link,
                "pub_date": pub_date,
            }
        )

        if len(items) >= MAX_ITEMS:
            break

    return items


def build_rss(items) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<rss version="2.0">')
    parts.append("<channel>")
    parts.append(f"<title>{escape('Victorian Labor - News')}</title>")
    parts.append(f"<link>{escape(NEWS_URL)}</link>")
    parts.append(
        f"<description>{escape('Unofficial feed generated from the Victorian Labor news page.')}</description>"
    )
    parts.append("<language>en-au</language>")
    parts.append(f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>")

    for item in items:
        guid = hashlib.sha1(item["link"].encode("utf-8")).hexdigest()
        parts.append("<item>")
        parts.append(f"<title>{escape(item['title'])}</title>")
        parts.append(f"<link>{escape(item['link'])}</link>")
        parts.append(f'<guid isPermaLink="false">{guid}</guid>')
        pub_date = item["pub_date"] or now
        parts.append(f"<pubDate>{format_datetime(pub_date)}</pubDate>")
        parts.append("</item>")

    parts.append("</channel>")
    parts.append("</rss>")
    return "\n".join(parts)


def main():
    try:
        html = fetch_html(NEWS_URL)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to fetch {NEWS_URL}: {exc}", file=sys.stderr)
        sys.exit(1)

    items = extract_items(html)
    if not items:
        print("No news items found - page structure may have changed.", file=sys.stderr)
        sys.exit(1)

    rss = build_rss(items)
    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"Wrote {len(items)} items to {FEED_PATH}")
    for item in items[:5]:
        print(" -", item["title"], "|", item["pub_date"], "|", item["link"])


if __name__ == "__main__":
    main()
