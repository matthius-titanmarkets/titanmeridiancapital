#!/usr/bin/env python3
"""Fetch market headlines from public RSS wires into platform/data/news.json.

Standard library only — safe to run in a bare GitHub Actions runner or locally:

    python3 scripts/fetch_news.py

The Meridian Terminal reads platform/data/news.json at load time. If this
script has never run (or a fetch fails entirely), the terminal falls back to
its built-in desk briefing items, so failure here is never user-visible
breakage — the wire just stays on seed content.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# Public, no-key RSS wires. Keep this list short and boring — every fetch is
# best-effort and any subset may fail without sinking the run.
FEEDS = [
    ("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("ForexLive", "https://www.forexlive.com/feed/news"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
]

MAX_ITEMS = 40
TIMEOUT_S = 15
OUT_PATH = Path(__file__).resolve().parent.parent / "platform" / "data" / "news.json"

TAG_RULES = [
    (re.compile(r"\b(fed|fomc|rate|inflation|cpi|ecb|boj|treasury|yield)\b", re.I), "macro"),
    (re.compile(r"\b(gold|silver|oil|crude|copper|commodit)\w*", re.I), "commodities"),
    (re.compile(r"\b(dollar|euro|yen|fx|currenc)\w*", re.I), "fx"),
    (re.compile(r"\b(stocks?|s&p|nasdaq|dow|equit|earnings)\w*", re.I), "equities"),
    (re.compile(r"\b(bitcoin|crypto|ethereum)\w*", re.I), "crypto"),
]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(raw: str) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(raw.strip())
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def tags_for(title: str) -> list[str]:
    tags = [tag for rx, tag in TAG_RULES if rx.search(title)]
    return tags or ["wire"]


def fetch_feed(source: str, url: str) -> list[dict]:
    req = urllib.request.Request(
        url, headers={"User-Agent": "MeridianTerminal-NewsFetch/1.0 (+github actions)"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        body = resp.read()
    root = ET.fromstring(body)

    items = []
    # RSS 2.0 <item> or Atom <entry>
    ns_atom = "{http://www.w3.org/2005/Atom}"
    for node in root.iter():
        if node.tag == "item":
            title = clean((node.findtext("title") or ""))
            link = (node.findtext("link") or "").strip()
            pub = node.findtext("pubDate") or node.findtext(
                "{http://purl.org/dc/elements/1.1/}date"
            ) or ""
        elif node.tag == f"{ns_atom}entry":
            title = clean(node.findtext(f"{ns_atom}title") or "")
            link_el = node.find(f"{ns_atom}link")
            link = (link_el.get("href") if link_el is not None else "") or ""
            pub = node.findtext(f"{ns_atom}updated") or ""
        else:
            continue
        if not title:
            continue
        items.append(
            {
                "title": title[:220],
                "source": source,
                "url": link,
                "published": parse_date(pub).isoformat().replace("+00:00", "Z"),
                "tags": tags_for(title),
            }
        )
    return items


def main() -> int:
    collected: list[dict] = []
    errors: list[str] = []
    for source, url in FEEDS:
        try:
            got = fetch_feed(source, url)
            collected.extend(got)
            print(f"[news] {source}: {len(got)} items")
        except Exception as exc:  # noqa: BLE001 — any single wire may fail freely
            errors.append(f"{source}: {exc}")
            print(f"[news] {source}: FAILED ({exc})", file=sys.stderr)

    if not collected:
        print("[news] every feed failed; leaving existing news.json untouched", file=sys.stderr)
        return 0  # keep the previous file (or seed) rather than clobbering it

    seen: set[str] = set()
    unique = []
    for item in sorted(collected, key=lambda i: i["published"], reverse=True):
        key = item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "live",
        "errors": errors,
        "items": unique[:MAX_ITEMS],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[news] wrote {len(payload['items'])} items -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
