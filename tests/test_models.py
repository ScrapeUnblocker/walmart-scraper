"""Unit tests for the data-shaping layer (no network)."""

from __future__ import annotations

from walmart_scraper.models import Product, SearchItem, csv_fieldnames


def test_search_item_from_parsed(sample_listing):
    item = SearchItem.from_parsed(sample_listing)
    assert item.item_id == "985675140"  # coerced to str
    assert item.name.startswith("BLACK+DECKER")
    assert item.url.endswith("/985675140")
    assert item.average_rating == 4.5
    assert item.number_of_reviews == 6253
    assert item.is_sponsored is False
    assert item.out_of_stock is False
    assert item.product_type == "Drip Coffee Makers"


def test_search_item_handles_missing_fields():
    item = SearchItem.from_parsed({"name": "Thing"})
    assert item.name == "Thing"
    assert item.item_id is None
    assert item.average_rating is None
    assert item.is_sponsored is None


def test_product_from_parsed_price_dict(sample_product):
    product = Product.from_parsed(sample_product, url="https://www.walmart.com/ip/985675140")
    assert product.price == 31.97
    assert product.currency == "USD"
    assert product.brand == "BLACK+DECKER"
    assert product.images == [
        "https://i5.walmartimages.com/seo/a.jpeg",
        "https://i5.walmartimages.com/asr/b.jpeg",
    ]


def test_product_from_parsed_bare_price_and_string_currency():
    product = Product.from_parsed({"title": "X", "price": "$1,299.00", "currency": "USD"})
    assert product.price == 1299.0
    assert product.currency == "USD"


def test_product_normalises_single_image_to_list():
    product = Product.from_parsed({"title": "X", "images": "one.jpg"})
    assert product.images == ["one.jpg"]


def test_number_coercion_from_strings():
    item = SearchItem.from_parsed(
        {"name": "X", "average_rating": "4.7", "number_of_reviews": "1,204"}
    )
    assert item.average_rating == 4.7
    assert item.number_of_reviews == 1204


def test_csv_fieldnames_are_stable():
    assert csv_fieldnames(SearchItem)[0] == "item_id"
    assert "price" in csv_fieldnames(Product)
