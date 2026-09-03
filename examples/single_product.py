"""Fetch one Walmart product page by URL or item id and print the details.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/single_product.py 985675140
"""

from __future__ import annotations

import json
import sys

from walmart_scraper import WalmartScraper


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "985675140"
    scraper = WalmartScraper()
    product = scraper.product(target)
    print(json.dumps(product.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
