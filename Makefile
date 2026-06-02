.PHONY: setup up migrate seed views scrapers api web test

setup:
	bash scripts/setup.sh

up:
	docker compose up -d

migrate:
	alembic -c db/alembic.ini upgrade head

seed:
	python db/seed.py

views:
	python analytics/apply_views.py

scrapers:
	bash scripts/run_scrapers.sh

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm install && npm run dev

test:
	cd scrapers && PYTHONPATH=.:.:. pytest ../scrapers/tests -q 2>/dev/null || \
	PYTHONPATH="scrapers:." python -m pytest scrapers/tests -q
