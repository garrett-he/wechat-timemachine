default:
    @just --list

init:
    uv sync

build:
    uv build

deploy:
    uv run nuitka src/wechat_timemachine/__main__.py \
    --onefile \
    --output-filename=wechat-timemachine \
    --output-dir=dist \
    --follow-imports

lint:
    uv run ruff check src/ tests/

publish:
    uv publish

test:
    uv run pytest --cov=src --cov-report=term-missing

format:
    uv run ruff format src/ tests/
