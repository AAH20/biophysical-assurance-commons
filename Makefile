.PHONY: test lint check

test:
	PYTHONPATH=packages/assurance-core/src python3 -m unittest discover -s packages/assurance-core/tests -v

lint:
	ruff check packages/assurance-core/src packages/assurance-core/tests
	ruff format --check packages/assurance-core/src packages/assurance-core/tests

check: lint test
