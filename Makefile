.PHONY: run-cloud run-selfhosted test docker-cloud docker-selfhosted

run-cloud:
	cp .env.cloud .env && uvicorn backend.main:app --reload --port 8000

run-selfhosted:
	cp .env.selfhosted .env && uvicorn backend.main:app --reload --port 8000

test:
	python -m pytest tests/ -v

docker-cloud:
	docker-compose -f docker-compose.yml up --build

docker-selfhosted:
	docker-compose -f docker-compose.self-hosted.yml up --build
