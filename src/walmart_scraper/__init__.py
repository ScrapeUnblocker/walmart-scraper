"""walmart_scraper - scrape Walmart search results and product details as clean JSON.

Powered by the ScrapeUnblocker getPageSource ``parsed_data`` API, which returns
AI-parsed structured JSON for a URL instead of raw HTML.

Example:
    >>> from walmart_scraper import WalmartScraper
    >>> scraper = WalmartScraper()               # reads SCRAPEUNBLOCKER_KEY
    >>> results = scraper.search("coffee maker", pages=1)
    >>> results[0].name
    'BLACK+DECKER Programmable 12-Cup Drip Coffee Maker'
    >>> product = scraper.product(results[0].url)
    >>> product.price, product.currency
    (31.97, 'USD')
"""

from __future__ import annotations

from .models import Product, SearchItem
from .scraper import WalmartScraper

__all__ = ["WalmartScraper", "SearchItem", "Product", "__version__"]

__version__ = "0.1.0"
