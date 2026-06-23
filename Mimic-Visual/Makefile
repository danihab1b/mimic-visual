# ===========================================================================
# Makefile — Docker convenience commands for Mimic-Visual
# ===========================================================================

.PHONY: help build up down logs shell pipeline render extract chunk embed index serve clean

DOCKER_COMPOSE := docker compose
IMAGE := visrag

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	$(DOCKER_COMPOSE) build api

up: ## Start API server (detached)
	$(DOCKER_COMPOSE) up -d api

down: ## Stop all services
	$(DOCKER_COMPOSE) down

logs: ## Tail API logs
	$(DOCKER_COMPOSE) logs -f api

status: ## Show running containers
	$(DOCKER_COMPOSE) ps

# ---------------------------------------------------------------------------
# Pipeline commands (run inside Docker)
# ---------------------------------------------------------------------------

pipeline: ## Run full pipeline: render -> extract -> chunk -> embed -> index
	$(DOCKER_COMPOSE) run --rm pipeline bash -c "\
		visrag render /app/pages/urls.txt -o /app/pages && \
		visrag extract /app/pages && \
		visrag chunk /app/pages && \
		visrag embed /app/pages && \
		visrag index build -i /app/pages -o /app/index"

render: ## Render documents: make render SOURCE=./urls.txt
	$(DOCKER_COMPOSE) run --rm pipeline visrag render $(SOURCE) -o /app/pages

extract: ## Extract text from rendered pages
	$(DOCKER_COMPOSE) run --rm pipeline visrag extract /app/pages

chunk: ## Chunk SDMs into slices
	$(DOCKER_COMPOSE) run --rm pipeline visrag chunk /app/pages

embed: ## Embed chunks into vectors
	$(DOCKER_COMPOSE) run --rm pipeline visrag embed /app/pages

index-build: ## Build FAISS index
	$(DOCKER_COMPOSE) run --rm pipeline visrag index build -i /app/pages -o /app/index

index-info: ## Show index statistics
	$(DOCKER_COMPOSE) run --rm pipeline visrag index info --index-dir /app/index

reconstruct: ## Reconstruct chunk: make reconstruct CHUNK_ID=abc123
	$(DOCKER_COMPOSE) run --rm pipeline visrag reconstruct $(CHUNK_ID) --index-dir /app/index

# ---------------------------------------------------------------------------
# Dev commands
# ---------------------------------------------------------------------------

shell: ## Open dev shell
	$(DOCKER_COMPOSE) run --rm dev

dev-up: ## Start dev environment
	$(DOCKER_COMPOSE) --profile dev up dev

clean: ## Remove all containers, volumes, images
	$(DOCKER_COMPOSE) down -v --rmi all
