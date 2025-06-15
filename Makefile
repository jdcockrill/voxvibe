# Root Makefile for Voice Flow Monorepo

.PHONY: app extension lint

app:
	cd app && uv sync && uv build

extension:
	cd extension && echo "See extension/README.md for manual GNOME extension install instructions."

lint:
	cd app && uv run ruff check
	# Add GNOME extension linting if JS lint config is added
