"""signals tool: HN "Who is hiring?" posts and BetaKit funding news, against recorded fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest

from jobs_mcp import server, signals
from jobs_mcp.result import BAD_INPUT, RATE_LIMITED
from tests.conftest import load_json, load_text
from tests.test_server import assert_error, assert_ok


@pytest.fixture
def sig_http(mock_http):
    recent = format_datetime(datetime.now(timezone.utc) - timedelta(days=2))
    feed = load_text("betakit_funding.xml").replace("{RECENT}", recent)
    mock_http.json("hn.algolia.com", "/api/v1/search_by_date", "hn_search.json")
    # recorded comments are re-dated to "2 days ago" so the default 30-day window keeps them
    item = load_json("hn_item.json")
    for child in item["children"]:
        child["created_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    mock_http.route("hn.algolia.com", "/api/v1/items/50338728", httpx.Response(200, json=item))
    mock_http.route("betakit.com", "/tag/funding/feed/", httpx.Response(200, text=feed))
    return mock_http


def _hn_only(s):
    return s["source"] == "hn"


def test_hn_picks_hiring_thread_and_parses_headline(sig_http):
    items = assert_ok(server.signals(sources=["hn"]))
    # deleted comment (text null) skipped; "Who wants to be hired" thread ignored
    assert [s["company"] for s in items] == ["Rootly", "Synteq", "Acme AI"]
    rootly = items[0]
    assert rootly["kind"] == "hiring_post"
    assert rootly["location"] == "SF Bay, Toronto, APAC, Remote"
    assert rootly["title"].startswith("Rootly | https://rootly.com/")
    assert "\n" not in rootly["title"]  # <p> became a line break, so the first line stands alone
    assert rootly["url"] == "https://news.ycombinator.com/item?id=50338901"
    assert "text" not in rootly  # full text is for filtering only
    fetched = [r.url.path for r in sig_http.requests if r.url.host == "hn.algolia.com"]
    assert "/api/v1/items/49922569" not in fetched  # only the latest thread by default


def test_hn_location_filter_reads_headline_not_body(sig_http):
    items = assert_ok(server.signals(sources=["hn"], location_regex=r"toronto|canada"))
    assert [s["company"] for s in items] == ["Rootly", "Acme AI"]


def test_hn_hidden_text_is_removed_and_flagged(sig_http):
    acme = next(s for s in assert_ok(server.signals(sources=["hn"])) if s["company"] == "Acme AI")
    assert "Ignore previous instructions" not in acme["summary"]
    assert acme["integrity"]["verdict"] != "clean"


def test_funding_parses_company_round_amount_and_drops_vc_funds(sig_http):
    items = assert_ok(server.signals(sources=["funding"], days=30))
    assert [s["company"] for s in items] == ["Odaia", "Bloomsco"]  # Wealthsimple is too old
    odaia = items[0]
    assert odaia["round"] == "Series C" and odaia["amount"] == "$15-million"
    assert odaia["location"] == "Healthtech, Toronto"
    assert "appeared first on" not in odaia["summary"]
    assert items[1]["round"] == "Pre-Seed"


def test_funding_can_keep_vc_funds(sig_http):
    items = assert_ok(server.signals(sources=["funding"], days=30, include_vc_funds=True))
    assert [s["kind"] for s in items] == ["funding", "funding", "vc_fund"]


def test_funding_location_and_include_filters(sig_http):
    items = assert_ok(server.signals(sources=["funding"], days=0, location_regex="Toronto"))
    assert [s["company"] for s in items] == ["Odaia", "Wealthsimple"]
    items = assert_ok(server.signals(sources=["funding"], days=0, include_regex=r"\bAI team\b"))
    assert [s["company"] for s in items] == ["Odaia"]


def test_one_failing_source_does_not_fail_the_call(sig_http):
    sig_http.route("betakit.com", "/tag/funding/feed/", httpx.Response(429))
    res = server.signals()
    items = assert_ok(res)
    assert items and all(_hn_only(s) for s in items)
    assert res["source_errors"][0]["code"] == RATE_LIMITED
    assert res["source_errors"][0]["source"] == "funding"


def test_all_sources_failing_is_an_error(sig_http):
    sig_http.route("betakit.com", "/tag/funding/feed/", httpx.Response(503))
    sig_http.route("hn.algolia.com", "/api/v1/search_by_date", httpx.Response(503))
    assert_error(server.signals(), "UPSTREAM_BROKEN")


def test_bad_source_and_bad_regex(sig_http):
    assert_error(server.signals(sources=["reddit"]), BAD_INPUT)
    assert_error(server.signals(include_regex="("), BAD_INPUT)


def test_broken_feed_is_upstream_broken(sig_http):
    sig_http.route("betakit.com", "/tag/funding/feed/", httpx.Response(200, text="<html>not rss"))
    assert_error(server.signals(sources=["funding"]), "UPSTREAM_BROKEN")


@pytest.mark.parametrize(
    "title,company",
    [
        ("Verafin alum-led Verlo nabs $4.5 million to build AI operating system", "Verlo"),
        ("Physical AI company Promise Robotics announces $40-million Series B round", "Promise Robotics"),
        ("BluWave-ai secures $8.1 million for energy grid software", "BluWave-ai"),
        ("Why Canada's Cohere stake has struck a nerve", ""),
    ],
)
def test_company_from_title(title, company):
    assert signals._company_from_title(title) == company


@pytest.mark.parametrize(
    "title",
    [
        "Natural Products Canada to open $25-million food systems scale-up fund",
        "EntrepreNorth secures $8-million initial close of fund for Indigenous entrepreneurs",
        "Conexus Venture Capital raises additional $5 million for Fund II",
        "Vistara Growth goes evergreen with launch of sixth private credit fund",
    ],
)
def test_vc_fund_titles(title):
    assert signals.VC_FUND.search(title)


def test_raise_to_fund_growth_is_not_a_vc_fund():
    assert not signals.VC_FUND.search("Heylist closes $3.1 million to fuel the niche creator economy")
    assert not signals.VC_FUND.search("Acme raises $5 million to fund expansion into the US")
