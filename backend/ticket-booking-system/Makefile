.PHONY: install test run server clean db-init

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

test:
	export PYTHONPATH=src && .venv/bin/pytest tests/ -v

test-cov:
	export PYTHONPATH=src && .venv/bin/pytest tests/ --cov=ticketbooking --cov-report=html

run:
	export PYTHONPATH=src && .venv/bin/python -m ticketbooking.main

server:
	export PYTHONPATH=src && .venv/bin/python -m ticketbooking.main

db-init:
	export PYTHONPATH=src && .venv/bin/python -c "from ticketbooking.api.server import init_db; from ticketbooking.config import Config; init_db(Config.from_env().database_url)"

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .venv
	rm -rf htmlcov
	rm -rf .coverage




