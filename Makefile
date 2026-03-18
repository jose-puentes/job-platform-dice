PYTHON ?= python
COMPOSE_FILE ?= infra/compose/docker-compose.yml

.PHONY: up down build logs lint test format

up:
	docker compose --env-file .env -f $(COMPOSE_FILE) up --build

down:
	docker compose --env-file .env -f $(COMPOSE_FILE) down

build:
	docker compose --env-file .env -f $(COMPOSE_FILE) build

logs:
	docker compose --env-file .env -f $(COMPOSE_FILE) logs -f

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m black .

test:
	$(PYTHON) -m pytest

