# walmart-scraper

[![CI](https://github.com/ScrapeUnblocker/walmart-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/ScrapeUnblocker/walmart-scraper/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Scrape **Walmart** search results and product details as clean, structured JSON —
name, price, currency, rating, reviews, brand, seller, availability, category and
images — with multi-page collection, product enrichment and CSV export.

Ships both a command-line tool and a small Python library.

> **Powered by [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos).**
> Walmart is served behind an anti-bot layer, so this project routes requests
> through the ScrapeUnblocker **getPageSource `parsed_data`** API, which loads the
> page in a real browser and returns AI-parsed JSON instead of raw HTML. You get
> structured fields directly — no CSS selectors to maintain.

## Features

- 🔎 **Search** — collect product tiles for any query, across multiple pages.
- 🏷️ **Product details** — price, currency, brand, rating count, dimensions, images.
- ➕ **Enrichment** — the search listing has no price; `--enrich` fetches each
  product page to fill it in.
- 🧾 **Export** — print JSON or write a CSV, from the CLI or the library.
- 🌍 **Country targeting** — route through a chosen proxy country (default `us`).
- 🔁 **Resilient** — automatic retry/backoff on transient bot walls and outages.
- 🧪 **Tested** — offline unit tests that mock the API (no credits spent in CI).

## Install

```bash
pip install .
# or, for a plain runtime install:
pip install -r requirements.txt
```

Get an API key from
[scrapeunblocker.com](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
and expose it (the SDK reads `SCRAPEUNBLOCKER_KEY`):

```bash
cp .env.example .env      # then edit it
export SCRAPEUNBLOCKER_KEY=your_key_here
```

## CLI usage

```bash
# Search and print JSON
walmart-scraper search "coffee maker" --pages 2 --pretty

# Search, enrich the top 5 with prices, save a spreadsheet
walmart-scraper search "coffee maker" --enrich --limit 5 --csv coffee.csv

# One product, by URL or by numeric item id
walmart-scraper product 985675140
walmart-scraper product "https://www.walmart.com/ip/.../985675140"

# Route through another country
walmart-scraper --country us search "air fryer"
```

## Library usage

```python
from walmart_scraper import WalmartScraper

scraper = WalmartScraper()                     # reads SCRAPEUNBLOCKER_KEY

# Search result tiles (no price on the listing page)
items = scraper.search("coffee maker", pages=1)
for item in items[:5]:
    print(item.name, "-", item.average_rating, "stars")

# Full product detail (has price)
product = scraper.product(items[0].url)
print(product.title, product.price, product.currency)

# Or do both in one call, capped at N product fetches
priced = scraper.search_and_enrich("coffee maker", pages=1, limit=5)
```

## Example output

A search item (`walmart-scraper search "coffee maker"`):

```json
{
  "item_id": "985675140",
  "product_id": "2PPLV83Y1QHE",
  "name": "BLACK+DECKER Programmable 12-Cup Drip Coffee Maker",
  "url": "https://www.walmart.com/ip/BLACK-DECKER-Coffeemaker/985675140",
  "image_url": "https://i5.walmartimages.com/seo/...jpeg",
  "average_rating": 4.5,
  "number_of_reviews": 6253,
  "availability_status": "In stock",
  "seller_name": "Walmart.com",
  "is_sponsored": false,
  "badge_text": "100+ bought since yesterday",
  "category_path": "Home Page/Home/Appliances/Kitchen Appliances/Coffee Makers",
  "product_type": "Drip Coffee Makers",
  "out_of_stock": false
}
```

A product (`walmart-scraper product 985675140`):

```json
{
  "url": "https://www.walmart.com/ip/985675140",
  "title": "BLACK+DECKER Programmable 12-Cup Drip Coffee Maker",
  "brand": "BLACK+DECKER",
  "price": 31.97,
  "currency": "USD",
  "rating_count": "6,253 ratings",
  "weight": "5.6 lb",
  "height": "12 in",
  "images": ["https://i5.walmartimages.com/seo/...jpeg"]
}
```

## Project layout

```
src/walmart_scraper/
  __init__.py      package exports + version
  models.py        SearchItem / Product dataclasses + parsing helpers
  scraper.py       WalmartScraper: search, product, enrich, pagination, retry
  cli.py           argparse command-line interface
examples/          runnable scripts (JSON, CSV, single product)
tests/             offline unit tests (mock the API - no credits spent)
```

## Development

```bash
make install       # pip install -e ".[dev]"
make lint          # ruff check .
make format        # ruff format + autofix
make test          # pytest -q
```

The test suite mocks the ScrapeUnblocker client, so it runs fully offline and
spends no API credit. CI runs lint + tests on Python 3.9 and 3.12.

## How it works

Each call goes to the ScrapeUnblocker
[`get_parsed`](https://developers.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
endpoint with a Walmart URL. The service renders the page and returns parsed
JSON; this library normalises those fields into typed `SearchItem` / `Product`
objects, handles multi-page collection, and retries transient failures. Because
parsing happens server-side, the scraper does not break when Walmart tweaks its
markup.

## Links

- 🌐 [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
- 📚 [API documentation](https://developers.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
- 🐍 [Python SDK](https://developers.scrapeunblocker.com/sdks/python?utm_source=github&utm_medium=integration&utm_campaign=example-repos)

## License

[MIT](LICENSE) © 2026 ScrapeUnblocker

---

This is an example integration. Please scrape responsibly and in accordance with
applicable laws and the target site's terms.
