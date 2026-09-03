"""Unit tests for the CLI arg parser and output formatting (no network)."""

from __future__ import annotations

import csv
import json

import pytest

from walmart_scraper import cli
from walmart_scraper.models import Product, SearchItem


class StubScraper:
    """Injected in place of WalmartScraper so the CLI never hits the network."""

    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        StubScraper.last_kwargs = kwargs

    def search(self, query, *, pages=1):
        return [SearchItem(item_id="1", name=f"{query} #{pages}", url="u")]

    def search_and_enrich(self, query, *, pages=1, limit=None):
        return [Product(title=query, price=9.99, currency="USD", images=["a", "b"])]

    def product(self, url_or_id):
        return Product(url=url_or_id, title="Widget", price=1.5, currency="USD")


@pytest.fixture(autouse=True)
def _patch_scraper(monkeypatch):
    monkeypatch.setattr(cli, "WalmartScraper", StubScraper)


def test_parser_requires_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_search_json_output(capsys):
    rc = cli.main(["search", "coffee maker", "--pages", "2"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["name"] == "coffee maker #2"


def test_country_flag_forwarded():
    cli.main(["--country", "de", "product", "123"])
    assert StubScraper.last_kwargs.get("proxy_country") == "de"


def test_search_enrich_uses_product_columns(capsys):
    rc = cli.main(["search", "coffee maker", "--enrich", "--limit", "1", "--pretty"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["price"] == 9.99


def test_product_json_output(capsys):
    rc = cli.main(["product", "985675140"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["title"] == "Widget"
    assert out[0]["url"] == "985675140"


def test_search_csv_output(tmp_path, capsys):
    out_file = tmp_path / "out.csv"
    rc = cli.main(["search", "coffee maker", "--csv", str(out_file)])
    assert rc == 0
    rows = list(csv.DictReader(out_file.open(encoding="utf-8")))
    assert rows[0]["name"] == "coffee maker #1"
    assert "item_id" in rows[0]


def test_enrich_csv_flattens_image_list(tmp_path):
    out_file = tmp_path / "p.csv"
    cli.main(["search", "q", "--enrich", "--csv", str(out_file)])
    rows = list(csv.DictReader(out_file.open(encoding="utf-8")))
    assert rows[0]["images"] == "a; b"
