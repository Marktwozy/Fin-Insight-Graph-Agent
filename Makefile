test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy src