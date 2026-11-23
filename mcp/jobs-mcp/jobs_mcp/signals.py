"""Hiring signals: companies that are hiring, or about to, before a posting reaches an ATS board.

Two public sources, no API keys:

  hn       the monthly "Ask HN: Who is hiring?" thread (HN Algolia API). Many small teams post
           there and nowhere else; each top-level comment is one company.
  funding  BetaKit's funding feed (Canadian startup news). A company that just closed a seed or
           Series A round usually grows its engineering team within a few months, often before
           any role is posted — the moment for a direct note to a founder or engineering lead.

Every item is a `Signal` dict: {source, kind, id, company, title, location, url, posted_at,
summary, ...}. Text from both sources is written by strangers, so it goes through the same
posting guard as job descriptions (`integrity` on each item).
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from . import boards
from .guard import compact, guard
from .result import NOT_FOUND, UPSTREAM_BROKEN, JobsError

HN_API = "https://hn.algolia.com/api/v1"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={}"
BETAKIT_FUNDING_FEED = "https://betakit.com/tag/funding/feed/"

_MAX_SUMMARY = 600

Signal = dict[str, Any]


def _guarded(raw: str | None, is_html: bool) -> tuple[str, dict[str, Any]]:
    if not raw:
        return "", {"verdict": "clean"}
    text, report = guard(raw, is_html=is_html)
    return text, compact(report)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _newer_than(posted_at: str | None, days: int) -> bool:
    if not posted_at or days <= 0:
        return True
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


# ------------------------------------------------------------------------ HN


_HN_TITLE = re.compile(r"^Ask HN: Who is hiring\?", re.I)


def hn_threads(months: int = 1) -> list[dict[str, Any]]:
    """The latest `months` "Who is hiring?" threads, newest first: [{id, title, created_at}]."""
    with boards._client() as c:
        r = c.get(
            f"{HN_API}/search_by_date",
            params={"tags": "story,author_whoishiring", "hitsPerPage": max(6, months * 3)},
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
    threads = [
        {"id": str(h["objectID"]), "title": h.get("title", ""), "created_at": h.get("created_at")}
        for h in hits
        if _HN_TITLE.search(h.get("title") or "")
    ]
    if not threads:
        raise JobsError(NOT_FOUND, "no 'Ask HN: Who is hiring?' thread found")
    return threads[:months]


def _hn_headline(text: str) -> str:
    return text.strip().split("\n", 1)[0].strip()


_WORK_MODE = re.compile(r"\b(?:remote|onsite|on-site|in-office|hybrid)\b", re.I)
_PLACE = re.compile(r"^[A-Z][\w .'’-]+,\s*[A-Z][\w .]+|\b(?:canada|toronto|vancouver|montr[eé]al)\b", re.I)
_ROLEISH = re.compile(
    r"engineer|developer|scientist|designer|manager|lead|position|role|intern|https?://|full[- ]time|"
    r"part[- ]time|contract|\$|€|£",
    re.I,
)


def _hn_fields(headline: str) -> tuple[str, str]:
    """Company and location from the 'Company | Role | Location | …' first line the thread asks
    for. Location = every segment naming a work mode (REMOTE / ONSITE / HYBRID) or a place
    ('Austin, TX', 'Toronto'), joined with ' | '."""
    parts = [p.strip() for p in headline.split("|") if p.strip()]
    company = parts[0][:80] if parts else ""
    locs = [
        p
        for p in parts[1:]
        if len(p) <= 80 and (_WORK_MODE.search(p) or (_PLACE.search(p) and not _ROLEISH.search(p)))
    ]
    return company, " | ".join(locs)[:160]


def hn_hiring(months: int = 1) -> list[Signal]:
    """One Signal per top-level comment in the latest `months` "Who is hiring?" threads."""
    out: list[Signal] = []
    with boards._client() as c:
        for t in hn_threads(months):
            r = c.get(f"{HN_API}/items/{t['id']}")
            r.raise_for_status()
            for child in r.json().get("children") or []:
                raw = child.get("text")
                if not raw or child.get("type") != "comment":  # deleted / flagged comments have no text
                    continue
                # HN separates paragraphs with a bare <p>; make it a line break so the
                # 'Company | Role | Location' first line stays its own line
                text, integrity = _guarded(re.sub(r"<p>", "\n\n<p>", raw), is_html=True)
                headline = _hn_headline(text)
                company, location = _hn_fields(headline)
                out.append(
                    {
                        "source": "hn",
                        "kind": "hiring_post",
                        "thread": t["title"],
                        "id": str(child["id"]),
                        "company": company,
                        "title": headline[:200],
                        "location": location,
                        "url": HN_ITEM_URL.format(child["id"]),
                        "posted_at": child.get("created_at"),
                        "summary": text[:_MAX_SUMMARY],
                        "text": text,
                        "integrity": integrity,
                    }
                )
    return out


# ------------------------------------------------------------------- funding

_RAISE_VERB = (
    r"raises|raised|closes|closed|secures|secured|nabs|lands|landed|banks|bags|scores|"
    r"announces|completes|snags|picks up|attracts|gets|emerges from stealth|wins"
)
_COMPANY_BEFORE_VERB = re.compile(rf"^(?P<company>.+?)\s+(?:{_RAISE_VERB})\b", re.I)
_ROUND = re.compile(r"\b(pre-?seed|seed|series [a-h]\b(?:\s*extension)?|bridge|growth round)", re.I)
_AMOUNT = re.compile(r"(?:US)?\$\s?\d[\d.,]*\s?(?:-?\s?(?:million|billion|M|B)\b)?(?:\s?(?:USD|CAD))?", re.I)
#: Announcements about investors (a new VC fund, a fund close), not companies that will hire.
VC_FUND = re.compile(
    r"\bfund (?:I{1,3}|IV|V|VI)\b|\b(?:new|second|third|debut|first|initial close of|close of|scale-up) "
    r"(?:\$[\d.,-]+\s?(?:million|billion)?\s)?fund\b|-(?:million|billion) (?:\w+ )?fund\b|"
    r"\bventure capital\b.*\b(?:raises|closes)\b|\bfund(?:s)? for\b|\b(?:credit|venture|vc) fund\b",
    re.I,
)


def _company_from_title(title: str) -> str:
    """'Verafin alum-led Verlo nabs $4.5 million …' → 'Verafin alum-led Verlo'. A guess; the
    full title is always kept, so the agent can correct it."""
    m = _COMPANY_BEFORE_VERB.search(title)
    if not m:
        return ""
    name = m.group("company").strip()
    # drop a descriptor prefix ("Physical AI company Promise Robotics" keeps the last capitalised run)
    m2 = re.search(r"((?:[A-Z0-9][\w.&'’-]*\s?)+)$", name)
    return (m2.group(1) if m2 else name).strip()[:80]


def funding_news(feed_url: str = BETAKIT_FUNDING_FEED) -> list[Signal]:
    """Funding announcements from an RSS feed (default: BetaKit's funding tag)."""
    with boards._client() as c:
        r = c.get(feed_url)
        r.raise_for_status()
        body = r.text
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise JobsError(UPSTREAM_BROKEN, f"funding feed was not valid RSS: {e}") from None
    out: list[Signal] = []
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        posted_at = None
        if item.findtext("pubDate"):
            try:
                posted_at = _iso(parsedate_to_datetime(item.findtext("pubDate")))
            except (TypeError, ValueError):
                posted_at = None
        categories = [html.unescape((cat.text or "").strip()) for cat in item.findall("category")]
        summary, integrity = _guarded(item.findtext("description"), is_html=True)
        summary = re.sub(r"\s*The post .*? appeared first on .*$", "", summary, flags=re.S).strip()
        text = f"{title}\n{summary}"
        rnd = _ROUND.search(text)
        amt = _AMOUNT.search(title) or _AMOUNT.search(summary)
        out.append(
            {
                "source": "betakit",
                "kind": "vc_fund" if VC_FUND.search(title) else "funding",
                "id": guid,
                "company": _company_from_title(title),
                "title": title,
                "location": ", ".join(c for c in categories if c not in {"Funding", "Briefs", "News"}),
                "round": rnd.group(1).title() if rnd else None,
                "amount": amt.group(0).strip() if amt else None,
                "categories": categories,
                "url": link,
                "posted_at": posted_at,
                "summary": summary[:_MAX_SUMMARY],
                "text": text,
                "integrity": integrity,
            }
        )
    return out


def to_public(s: Signal) -> Signal:
    """A Signal without the full `text` (kept only for filtering)."""
    return {k: v for k, v in s.items() if k != "text"}


newer_than = _newer_than
