.PHONY: setup hooks lint develop

setup:
	uv sync

hooks:
	uv run prek install

lint:
	uv run prek run --show-diff-on-failure --color=always

develop:
	@if [ ! -d "$(PWD)/config" ]; then \
		mkdir -p "$(PWD)/config"; \
		PYTHONPATH="$(PWD)/custom_components" uv run hass --config "$(PWD)/config" --script ensure_config; \
	fi
	PYTHONPATH="$(PWD)/custom_components" uv run hass --config "$(PWD)/config" --debug
