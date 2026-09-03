"""Typed containers for the data returned by :mod:`walmart_scraper`.

The ScrapeUnblocker ``parsed_data`` API returns plain dictionaries. These small
dataclasses give the scraped fields names, sane defaults, and a stable
``to_dict()`` shape for JSON/CSV export, so downstream code does not depend on
the exact key names the upstream parser happens to use.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


def _pick(data: dict[str, Any], *keys: str) -> Any:
    """Return the first present, non-None value among ``keys`` (or None)."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


@dataclass
class SearchItem:
    """One product tile from a Walmart search results page.

    Note: Walmart's search listing does not expose a price - fetch the product
    page (:meth:`WalmartScraper.product`) to get price and currency.
    """

    item_id: str | None = None
    product_id: str | None = None
    name: str | None = None
    url: str | None = None
    image_url: str | None = None
    average_rating: float | None = None
    number_of_reviews: int | None = None
    availability_status: str | None = None
    seller_name: str | None = None
    is_sponsored: bool | None = None
    badge_text: str | None = None
    category_path: str | None = None
    product_type: str | None = None
    out_of_stock: bool | None = None

    @classmethod
    def from_parsed(cls, data: dict[str, Any]) -> SearchItem:
        """Build a :class:`SearchItem` from one raw parsed listing dict."""
        return cls(
            item_id=_stringify(_pick(data, "item_id", "id")),
            product_id=_pick(data, "product_id", "us_item_id"),
            name=_pick(data, "name", "title"),
            url=_pick(data, "canonical_url", "url", "product_url"),
            image_url=_pick(data, "image_url", "image", "thumbnail"),
            average_rating=_to_float(_pick(data, "average_rating", "rating")),
            number_of_reviews=_to_int(_pick(data, "number_of_reviews", "review_count")),
            availability_status=_pick(data, "availability_status", "availability"),
            seller_name=_pick(data, "seller_name", "seller"),
            is_sponsored=_to_bool(_pick(data, "is_sponsored", "sponsored")),
            badge_text=_pick(data, "badge_text", "badge"),
            category_path=_pick(data, "category_path", "category"),
            product_type=_pick(data, "catalog_product_type", "product_type"),
            out_of_stock=_to_bool(_pick(data, "is_out_of_stock", "out_of_stock")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Product:
    """Detailed data from a single Walmart product page."""

    url: str | None = None
    title: str | None = None
    brand: str | None = None
    price: float | None = None
    currency: str | None = None
    rating_count: str | None = None
    weight: str | None = None
    height: str | None = None
    description: str | None = None
    images: list[str] = field(default_factory=list)

    @classmethod
    def from_parsed(cls, data: dict[str, Any], url: str | None = None) -> Product:
        """Build a :class:`Product` from a raw parsed product_detail dict."""
        price_value, price_currency = _split_price(data.get("price"))
        currency = price_currency or _pick(data, "currency")
        images = data.get("images") or []
        if not isinstance(images, list):
            images = [images]
        return cls(
            url=url,
            title=_pick(data, "title", "name"),
            brand=_pick(data, "brand"),
            price=price_value,
            currency=currency,
            rating_count=_stringify(_pick(data, "rating_count", "number_of_reviews")),
            weight=_pick(data, "weight"),
            height=_pick(data, "height"),
            description=_pick(data, "description"),
            images=[str(i) for i in images if i],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _split_price(price: Any) -> tuple[float | None, str | None]:
    """Normalise the ``price`` field, which may be a dict or a bare number."""
    if isinstance(price, dict):
        return _to_float(price.get("value")), price.get("currency")
    return _to_float(price), None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _stringify(value: Any) -> str | None:
    return None if value is None else str(value)


def csv_fieldnames(dataclass_type: type) -> list[str]:
    """Column order for CSV export of a dataclass."""
    return [f.name for f in fields(dataclass_type)]
