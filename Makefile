# Developer tasks.
# Structurizr and the IR check run through Docker Compose, so their pinned image tags live only in docker-compose.yml.

COMPOSE     ?= docker compose
STRUCTURIZR := $(COMPOSE) run --rm structurizr
PYTHON      ?= python
DOCS_BUILD  := docs/build

# Structurizr runs as the host user, so that on Linux it can write docs/architecture and docs/build; Python on
# Windows has no getuid, and the image's own user (65532) is kept there. Only the targets that start Structurizr
STRUCTURIZR_TARGETS := docs-up docs-down docs-validate docs-inspect docs-export docs-check
$(STRUCTURIZR_TARGETS): export DOCS_UID = $(shell $(PYTHON) -c "import os; print(os.getuid() if hasattr(os, 'getuid') else 65532)")
$(STRUCTURIZR_TARGETS): export DOCS_GID = $(shell $(PYTHON) -c "import os; print(os.getgid() if hasattr(os, 'getgid') else 65532)")

# Git Bash on Windows rewrites arguments that look like POSIX paths; container paths must pass through unchanged.
export MSYS_NO_PATHCONV := 1

.DEFAULT_GOAL := help

.PHONY: help docs-up docs-down docs-validate docs-inspect docs-export docs-link docs-check docs-build-dir ir-check \n	go-test go-lint go-check py-check check

help: ## List the available targets
	@$(PYTHON) -c "import re; [print(f'{m[1]:<15} {m[2]}') for m in re.finditer(r'^([a-z][a-z-]+):.*?## (.+)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

# --- Architecture documentation (docs/architecture, Structurizr) ---

docs-up: docs-build-dir ## Start Structurizr local on http://localhost:8080 (STRUCTURIZR_PORT overrides)
	$(COMPOSE) --profile docs up -d structurizr

docs-down: ## Stop Structurizr local
	$(COMPOSE) --profile docs down

docs-validate: docs-build-dir ## Validate the workspace
	$(STRUCTURIZR) validate -workspace workspace.dsl

docs-inspect: docs-build-dir ## Run Structurizr inspections (report-only)
	-$(STRUCTURIZR) inspect -workspace workspace.dsl

# Every target that starts the container depends on this one: Docker creates a missing bind-mount folder as root,
# which the container's user cannot write on Linux, so docs/build is created first, by the host user.
docs-build-dir:
	@$(PYTHON) -c "import os, pathlib, sys; p = pathlib.Path('$(DOCS_BUILD)'); p.mkdir(parents=True, exist_ok=True); os.access(p, os.W_OK) or sys.exit(f'{p} is not writable by this user; Docker may have created it as root. Remove it and run make again.')"

docs-export: docs-build-dir ## Export the workspace as JSON and as a static site to docs/build
	$(STRUCTURIZR) export -workspace workspace.dsl -format json -output /usr/local/build/json
	$(STRUCTURIZR) export -workspace workspace.dsl -format static -output /usr/local/build/site

docs-link: ## Turn bare references (D29, S25, CORE 2.6) into links, in docs/architecture and docs/ir
	$(PYTHON) tools/docs/link.py --root docs/architecture

docs-check: docs-validate ## Validate, then run the documentation checks
	$(STRUCTURIZR) export -workspace workspace.dsl -format json -output /usr/local/build/json
	$(PYTHON) tools/docs/check.py --root docs/architecture --workspace-json $(DOCS_BUILD)/json/workspace.json
	$(PYTHON) tools/docs/link.py --root docs/architecture --check

# --- IR specification (docs/ir) and its schema ---

ir-check: ## Check the IR schema and its conformance corpus
	$(COMPOSE) run --rm ir-check

# --- Go: control plane, agent, CLI ---

go-test: ## test the Go module
	go test ./...

go-lint: ## Lint and check formatting with golangci-lint
	$(COMPOSE) run --rm go-lint

go-check: go-test go-lint ## Run every Go check

# --- Python: unit runtime and SDK ---

py-check: ## Lint, format-check, type-check and test the Python workspace
	uv sync --locked
	uv run ruff check
	uv run ruff format --check
	uv run pyright
	uv run pytest

# --- Everything ---

check: docs-check ir-check go-check py-check ## Run every check a commit must pass
