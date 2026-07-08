.PHONY: run test migrate revision docker-up docker-down

run:
	uvicorn app.main:app --reload

test:
	pytest --cov=app tests/ -v

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
