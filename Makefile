.PHONY: install lint format test run clean

install:
	pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest -q

run:
	walmart-scraper search "coffee maker" --pages 1 --pretty

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
