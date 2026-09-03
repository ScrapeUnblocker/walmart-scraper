"""Search Walmart and print the listing tiles as JSON.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here   # get one at scrapeunblocker.com
    python examples/search_to_json.py "coffee maker"
"""

from __future__ import annotations

import json
import sys

from walmart_scraper import WalmartScraper


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "coffee maker"
    scraper = WalmartScraper()
    items = scraper.search(query, pages=1)
    print(f"Found {len(items)} items for {query!r}\n")
    print(json.dumps([i.to_dict() for i in items[:10]], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
