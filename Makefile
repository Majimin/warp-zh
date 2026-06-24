.PHONY: install test lint fmt check clean build help

help:
	@echo "make install   安装开发依赖"
	@echo "make test      运行所有测试"
	@echo "make lint      代码检查"
	@echo "make check     lint + test"
	@echo "make build     构建 wheel"
	@echo "make clean     清理产物"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=warp_zh --cov-report=term-missing

test-quick:
	pytest tests/ -q

lint:
	ruff check warp_zh/ tests/
	mypy warp_zh/ --ignore-missing-imports

fmt:
	ruff format warp_zh/ tests/

check: lint test

build:
	pip install build && python -m build

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
