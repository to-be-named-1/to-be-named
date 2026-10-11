# Developer tasks.
# Structurizr runs through Docker Compose, so its pinned image tag lives only in docker-compose.yml.

COMPOSE     ?= docker compose
STRUCTURIZR := $(COMPOSE) run --rm structurizr
PYTHON      ?= python
DOCS_BUILD  := docs/build

# Git Bash on Windows rewrites arguments that look like POSIX paths; container paths must pass through unchanged.
export MSYS_NO_PATHCONV := 1

.DEFAULT_GOAL := help

.PHONY: help docs-up docs-down docs-validate docs-inspect docs-export docs-check

help: ## List the available targets
	@$(PYTHON) -c "import re; [print(f'{m[1]:<15} {m[2]}') for m in re.finditer(r'^([a-z][a-z-]+):.*?## (.+)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

# --- Architecture documentation (docs/architecture, Structurizr) ---

docs-up: ## Start Structurizr local on http://localhost:8080 (STRUCTURIZR_PORT overrides)
	$(COMPOSE) --profile docs up -d structurizr

docs-down: ## Stop Structurizr local
	$(COMPOSE) --profile docs down

docs-validate: ## Validate the workspace
	$(STRUCTURIZR) validate -workspace workspace.dsl

docs-inspect: ## Run Structurizr inspections (report-only)
	-$(STRUCTURIZR) inspect -workspace workspace.dsl

docs-export: ## Export the workspace as JSON and as a static site to docs/build
	$(STRUCTURIZR) export -workspace workspace.dsl -format json -output /usr/local/build/json
	$(STRUCTURIZR) export -workspace workspace.dsl -format static -output /usr/local/build/site

docs-check: docs-validate ## Validate, then run the documentation checks
	$(STRUCTURIZR) export -workspace workspace.dsl -format json -output /usr/local/build/json
	$(PYTHON) tools/docs/check.py --root docs/architecture --workspace-json $(DOCS_BUILD)/json/workspace.json
