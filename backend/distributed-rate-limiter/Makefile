PYTHON ?= python3
VENV ?= .venv
PROTO_SRC = proto/rate_limiter.proto
PROTO_PY_OUT = src

.PHONY: venv
venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: proto
proto:
	$(PYTHON) -m grpc_tools.protoc -Iproto --python_out=$(PROTO_PY_OUT) --grpc_python_out=$(PROTO_PY_OUT) $(PROTO_SRC)

.PHONY: run
run:
	$(PYTHON) -m ratelimiter.server

.PHONY: test
test:
	$(PYTHON) -m pytest

