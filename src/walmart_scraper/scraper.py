"""Core scraping logic for Walmart search results and product pages.

Everything routes through the ScrapeUnblocker ``get_parsed`` endpoint (the
getPageSource ``parsed_data`` API), which handles the anti-bot layer and returns
clean, AI-parsed JSON. This module only shapes and paginates that output.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import quote_plus, urlparse

from scrapeunblocker import BlockedError, Client, ScrapeUnblockerError, UpstreamOutageError

from .models import Product, SearchItem

SEARCH_URL = "https://www.walmart.com/search"
PRODUCT_URL = "https://www.walmart.com/ip/{item_id}"

# Transient upstream conditions that are worth another attempt. The SDK already
# retries network/5xx errors internally; these are the page-level ones it does
# not (a bot wall or a temporary upstream outage on the target site).
_RETRYABLE = (BlockedError, UpstreamOutageError)

_ITEM_ID_RE = re.compile(r"/ip/(?:.*/)?(\d+)")


class WalmartScraper:
    """Scrape Walmart via the ScrapeUnblocker parsed_data API.

    Args:
        client: A pre-built ``scrapeunblocker.Client``. If omitted, one is
            created from the ``SCRAPEUNBLOCKER_KEY`` environment variable.
        proxy_country: ISO country to route requests through (default ``"us"``;
            Walmart is US-centric, so a US exit keeps prices in USD).
        max_retries: Extra attempts for page-level bot walls / upstream outages.
        retry_backoff: Base seconds for exponential backoff between retries.
        api_key: Optional explicit key, forwarded to ``Client`` when no client
            is supplied.
        sleep: Injectable sleep function (used by tests to avoid real waits).
    """

    def __init__(
        self,
        client: Client | None = None,
        *,
        proxy_country: str = "us",
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        api_key: str | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.client = client or Client(api_key=api_key)
        self.proxy_country = proxy_country
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._sleep = sleep

    # -- public API ---------------------------------------------------------

    def search(self, query: str, *, pages: int = 1) -> list[SearchItem]:
        """Search Walmart and return listing tiles across ``pages`` result pages.

        Pagination stops early when a page yields no new items (Walmart does not
        return a reliable ``next_page`` cursor, so we page by URL and de-dupe).
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        pages = max(1, pages)

        items: list[SearchItem] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            parsed = self._fetch(self._search_url(query, page))
            raw_items = _listing_items(parsed.data)
            if not raw_items:
                break
            new_on_page = 0
            for raw in raw_items:
                item = SearchItem.from_parsed(raw)
                key = item.item_id or item.url or item.name
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                items.append(item)
                new_on_page += 1
            if new_on_page == 0:
                break
        return items

    def product(self, url_or_id: str) -> Product:
        """Fetch and shape a single Walmart product page.

        Accepts a full Walmart product URL (e.g. the ``url`` of a search item)
        or a bare numeric item id.
        """
        url = self._product_url(url_or_id)
        parsed = self._fetch(url)
        data = parsed.data if isinstance(parsed.data, dict) else {}
        return Product.from_parsed(data, url=url)

    def search_and_enrich(
        self, query: str, *, pages: int = 1, limit: int | None = None
    ) -> list[Product]:
        """Search, then fetch each product page to attach currency and details.

        The search listing has the price but not its currency, brand or images.
        ``limit`` caps how many products are enriched (each product page is one
        extra API call).
        """
        listings = self.search(query, pages=pages)
        if limit is not None:
            listings = listings[:limit]
        products: list[Product] = []
        for listing in listings:
            if not listing.url:
                continue
            product = self.product(listing.url)
            if product.title is None:
                product.title = listing.name
            products.append(product)
        return products

    # -- internals ----------------------------------------------------------

    def _search_url(self, query: str, page: int) -> str:
        url = f"{SEARCH_URL}?q={quote_plus(query)}"
        if page > 1:
            url += f"&page={page}"
        return url

    def _product_url(self, url_or_id: str) -> str:
        value = str(url_or_id).strip()
        if value.startswith("http://") or value.startswith("https://"):
            host = urlparse(value).netloc.lower()
            if "walmart." not in host:
                raise ValueError(f"not a Walmart URL: {value}")
            return value
        if value.isdigit():
            return PRODUCT_URL.format(item_id=value)
        match = _ITEM_ID_RE.search(value)
        if match:
            return PRODUCT_URL.format(item_id=match.group(1))
        raise ValueError(f"expected a Walmart product URL or numeric item id, got: {value!r}")

    def _fetch(self, url: str) -> Any:
        """Call ``get_parsed`` with a small retry loop for page-level failures."""
        last_error: ScrapeUnblockerError | None = None
        for attempt in range(self.max_retries):
            try:
                return self.client.get_parsed(url, proxy_country=self.proxy_country)
            except _RETRYABLE as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    self._sleep(self.retry_backoff * (2**attempt))
        assert last_error is not None
        raise last_error


def _listing_items(data: Any) -> list[dict[str, Any]]:
    """Pull the list of product dicts out of a parsed search payload."""
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if isinstance(items, list):
        return [i for i in items if isinstance(i, dict)]
    return []
