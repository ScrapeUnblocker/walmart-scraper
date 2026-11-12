"""Command-line interface for walmart_scraper.

Usage:
    walmart-scraper search "coffee maker" --pages 2 --csv out.csv
    walmart-scraper search "coffee maker" --enrich --limit 5 --json
    walmart-scraper product https://www.walmart.com/ip/.../985675140
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Sequence
from typing import Any

from scrapeunblocker import ScrapeUnblockerError

from . import __version__
from .models import Product, SearchItem, csv_fieldnames
from .scraper import WalmartScraper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="walmart-scraper",
        description="Scrape Walmart search results and product details as clean JSON, "
        "powered by ScrapeUnblocker.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--country",
        default="us",
        metavar="ISO",
        help="Proxy country to route through (default: us).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search Walmart and list matching products.")
    search.add_argument("query", help='Search terms, e.g. "coffee maker".')
    search.add_argument(
        "--pages", type=int, default=1, help="Number of result pages to collect (default: 1)."
    )
    search.add_argument(
        "--enrich",
        action="store_true",
        help="Fetch each product page to add currency/brand/images (extra API calls).",
    )
    search.add_argument(
        "--limit",
        type=int,
        default=None,
        help="With --enrich, cap how many products to fetch in detail.",
    )
    _add_output_args(search)

    product = sub.add_parser("product", help="Fetch details for one product URL or item id.")
    product.add_argument("url_or_id", help="A Walmart product URL or numeric item id.")
    _add_output_args(product)

    return parser


def _add_output_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--json", action="store_true", help="Print JSON (default).")
    sub.add_argument("--csv", metavar="PATH", help="Write results to a CSV file at PATH.")
    sub.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scraper = WalmartScraper(proxy_country=args.country)

    try:
        if args.command == "search":
            rows = _run_search(scraper, args)
            model = Product if args.enrich else SearchItem
        else:
            rows = [scraper.product(args.url_or_id).to_dict()]
            model = Product
    except ScrapeUnblockerError as exc:
        print(f"error: ScrapeUnblocker request failed: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.csv:
        _write_csv(args.csv, rows, csv_fieldnames(model))
        print(f"Wrote {len(rows)} row(s) to {args.csv}", file=sys.stderr)
    else:
        indent = 2 if args.pretty else None
        print(json.dumps(rows, indent=indent, ensure_ascii=False))
    return 0


def _run_search(scraper: WalmartScraper, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.enrich:
        products = scraper.search_and_enrich(args.query, pages=args.pages, limit=args.limit)
        return [p.to_dict() for p in products]
    items = scraper.search(args.query, pages=args.pages)
    return [i.to_dict() for i in items]


def _write_csv(path: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _flatten(v) for k, v in row.items()})


def _flatten(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return value


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
