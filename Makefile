.PHONY: setup lint fix develop

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format . --check
	uv run ty check custom_components/

fix:
	uv run ruff check . --fix
	uv run ruff format .

develop:
	@if [ ! -d "$(PWD)/config" ]; then \
		mkdir -p "$(PWD)/config"; \
		PYTHONPATH="$(PWD)/custom_components" uv run hass --config "$(PWD)/config" --script ensure_config; \
	fi
	PYTHONPATH="$(PWD)/custom_components" uv run hass --config "$(PWD)/config" --debug
