"""Shared test fixtures and a fake ScrapeUnblocker client (no network / no credit)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class FakePage:
    """Stand-in for scrapeunblocker.ParsedPage."""

    data: dict[str, Any]
    page_type: str = "search_list"
    source: str = "test"
    raw: dict[str, Any] = field(default_factory=dict)


class FakeClient:
    """Records calls and returns queued pages (or raises queued exceptions)."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def get_parsed(self, url: str, **kwargs: Any) -> Any:
        self.calls.append({"url": url, **kwargs})
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def search_page(items: list[dict[str, Any]]) -> FakePage:
    return FakePage(data={"items": items, "total": len(items), "next_page": None})


def product_page(data: dict[str, Any]) -> FakePage:
    return FakePage(data=data, page_type="product_detail")


@pytest.fixture
def sample_listing() -> dict[str, Any]:
    return {
        "item_id": 985675140,
        "product_id": "2PPLV83Y1QHE",
        "name": "BLACK+DECKER Programmable 12-Cup Drip Coffee Maker",
        "canonical_url": "https://www.walmart.com/ip/BLACK-DECKER-Coffeemaker/985675140",
        "image_url": "https://i5.walmartimages.com/seo/x.jpeg",
        "average_rating": 4.5,
        "number_of_reviews": 6253,
        "availability_status": "In stock",
        "seller_name": "Walmart.com",
        "is_sponsored": False,
        "badge_text": "100+ bought since yesterday",
        "category_path": "Home/Appliances/Coffee Makers",
        "catalog_product_type": "Drip Coffee Makers",
        "is_out_of_stock": False,
    }


@pytest.fixture
def sample_product() -> dict[str, Any]:
    return {
        "title": "BLACK+DECKER Programmable 12-Cup Drip Coffee Maker",
        "description": "Buy BLACK+DECKER Programmable 12-Cup Drip Coffee Maker at Walmart.com",
        "price": {"value": 31.97, "currency": "USD"},
        "currency": "USD",
        "rating_count": "6,253 ratings",
        "brand": "BLACK+DECKER",
        "weight": "5.6 lb",
        "height": "12 in",
        "images": [
            "https://i5.walmartimages.com/seo/a.jpeg",
            "https://i5.walmartimages.com/asr/b.jpeg",
        ],
    }
