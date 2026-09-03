"""Unit tests for pagination, URL building and retry logic (no network)."""

from __future__ import annotations

import pytest
from conftest import FakeClient, product_page, search_page
from scrapeunblocker import BlockedError, ScrapeTimeoutError, UpstreamOutageError

from walmart_scraper import WalmartScraper


def _scraper(responses, **kwargs):
    kwargs.setdefault("sleep", lambda _s: None)  # never actually wait in tests
    return WalmartScraper(client=FakeClient(responses), **kwargs)


def test_search_shapes_items(sample_listing):
    scraper = _scraper([search_page([sample_listing])])
    items = scraper.search("coffee maker")
    assert len(items) == 1
    assert items[0].name.startswith("BLACK+DECKER")


def test_search_url_encodes_query_and_paginates(sample_listing):
    client = FakeClient([search_page([sample_listing]), search_page([{"item_id": 2, "name": "B"}])])
    scraper = WalmartScraper(client=client, sleep=lambda _s: None)
    scraper.search("coffee maker", pages=2)
    assert client.calls[0]["url"] == "https://www.walmart.com/search?q=coffee+maker"
    assert client.calls[1]["url"] == "https://www.walmart.com/search?q=coffee+maker&page=2"
    assert client.calls[0]["proxy_country"] == "us"


def test_search_dedupes_across_pages(sample_listing):
    # Same item returned on both pages -> only counted once.
    scraper = _scraper([search_page([sample_listing]), search_page([sample_listing])])
    items = scraper.search("coffee maker", pages=2)
    assert len(items) == 1


def test_search_stops_on_empty_page(sample_listing):
    client = FakeClient([search_page([sample_listing]), search_page([])])
    scraper = WalmartScraper(client=client, sleep=lambda _s: None)
    items = scraper.search("coffee maker", pages=5)
    assert len(items) == 1
    assert len(client.calls) == 2  # did not fetch pages 3-5


def test_search_rejects_empty_query():
    scraper = _scraper([])
    with pytest.raises(ValueError):
        scraper.search("   ")


def test_product_by_id_builds_url(sample_product):
    client = FakeClient([product_page(sample_product)])
    scraper = WalmartScraper(client=client, sleep=lambda _s: None)
    product = scraper.product("985675140")
    assert client.calls[0]["url"] == "https://www.walmart.com/ip/985675140"
    assert product.price == 31.97


def test_product_accepts_full_url(sample_product):
    url = "https://www.walmart.com/ip/BLACK-DECKER/985675140"
    client = FakeClient([product_page(sample_product)])
    scraper = WalmartScraper(client=client, sleep=lambda _s: None)
    scraper.product(url)
    assert client.calls[0]["url"] == url


def test_product_extracts_id_from_path(sample_product):
    scraper = _scraper([product_page(sample_product)])
    # A relative path with an embedded id should still resolve.
    product = scraper.product("/ip/Some-Slug/985675140")
    assert product.title is not None


def test_product_rejects_non_walmart_url():
    scraper = _scraper([])
    with pytest.raises(ValueError):
        scraper.product("https://www.amazon.com/dp/B08N5WRWNW")


def test_product_rejects_garbage():
    scraper = _scraper([])
    with pytest.raises(ValueError):
        scraper.product("not-a-url")


def test_fetch_retries_on_blocked_then_succeeds(sample_listing):
    responses = [
        BlockedError("blocked", status_code=403),
        UpstreamOutageError("upstream", status_code=502),
        search_page([sample_listing]),
    ]
    client = FakeClient(responses)
    scraper = WalmartScraper(client=client, max_retries=3, sleep=lambda _s: None)
    items = scraper.search("coffee maker")
    assert len(items) == 1
    assert len(client.calls) == 3


def test_fetch_gives_up_after_max_retries():
    responses = [BlockedError("blocked", status_code=403)] * 3
    client = FakeClient(responses)
    scraper = WalmartScraper(client=client, max_retries=3, sleep=lambda _s: None)
    with pytest.raises(BlockedError):
        scraper.search("coffee maker")
    assert len(client.calls) == 3


def test_fetch_does_not_retry_unknown_errors():
    # ScrapeTimeoutError is not in the page-level retry set -> propagate immediately.
    client = FakeClient([ScrapeTimeoutError("timeout")])
    scraper = WalmartScraper(client=client, max_retries=3, sleep=lambda _s: None)
    with pytest.raises(ScrapeTimeoutError):
        scraper.search("coffee maker")
    assert len(client.calls) == 1


def test_search_and_enrich(sample_listing, sample_product):
    responses = [search_page([sample_listing]), product_page(sample_product)]
    scraper = _scraper(responses)
    products = scraper.search_and_enrich("coffee maker", limit=1)
    assert len(products) == 1
    assert products[0].price == 31.97
