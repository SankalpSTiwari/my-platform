.PHONY: install test run server frontend clean

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

test:
	export PYTHONPATH=src && .venv/bin/pytest tests/ -v

test-cov:
	export PYTHONPATH=src && .venv/bin/pytest tests/ --cov=logsearch --cov-report=html

run:
	export PYTHONPATH=src && .venv/bin/python -m logsearch.main

server:
	export PYTHONPATH=src && .venv/bin/python -m logsearch.main

frontend-install:
	cd frontend && npm install

frontend:
	cd frontend && npm start

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .venv
	rm -rf frontend/node_modules
	rm -rf frontend/build
	rm -rf htmlcov
	rm -rf .coverage

