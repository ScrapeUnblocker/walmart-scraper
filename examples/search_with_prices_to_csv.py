"""Search Walmart, enrich the top results with product-page prices, save a CSV.

The search listing does not include a price, so this fetches each product page
to fill in price, currency, brand and images - then writes a spreadsheet.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/search_with_prices_to_csv.py "coffee maker" prices.csv
"""

from __future__ import annotations

import csv
import sys

from walmart_scraper import WalmartScraper
from walmart_scraper.models import Product, csv_fieldnames


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "coffee maker"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "prices.csv"

    scraper = WalmartScraper()
    products = scraper.search_and_enrich(query, pages=1, limit=5)

    fieldnames = csv_fieldnames(Product)
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for product in products:
            row = product.to_dict()
            row["images"] = "; ".join(row.get("images") or [])
            writer.writerow(row)

    for product in products:
        price = f"{product.price} {product.currency}" if product.price else "n/a"
        print(f"{price:>12}  {product.title}")
    print(f"\nWrote {len(products)} rows to {out_path}")


if __name__ == "__main__":
    main()
