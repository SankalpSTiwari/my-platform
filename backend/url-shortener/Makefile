.PHONY: install run test clean db-init

install:
	pip install -r requirements.txt

run:
	export PYTHONPATH=src && python -m urlshortener.main

db-init:
	export PYTHONPATH=src && python -c "from urlshortener.shared.models.database import init_db; from urlshortener.shared.config import Config; init_db(Config.from_env().database_url)"

test:
	export PYTHONPATH=src && python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

