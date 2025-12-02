.PHONY: help install dev clean lint format check test run all

# 默认目标
help:
	@echo "SimpleLLMFront - UV + Ruff 管理命令"
	@echo ""
	@echo "安装与环境:"
	@echo "  make install      - 安装生产依赖"
	@echo "  make dev          - 安装开发依赖"
	@echo "  make clean        - 清理缓存和临时文件"
	@echo ""
	@echo "代码质量:"
	@echo "  make lint         - 运行 Ruff 检查 (不修复)"
	@echo "  make lint-fix     - 运行 Ruff 检查并自动修复"
	@echo "  make format       - 格式化代码"
	@echo "  make format-check - 检查代码格式 (不修改)"
	@echo "  make check        - 完整检查 (lint + format check)"
	@echo "  make fix          - 完整修复 (lint fix + format)"
	@echo ""
	@echo "测试与运行:"
	@echo "  make test         - 运行测试"
	@echo "  make test-cov     - 运行测试并生成覆盖率报告"
	@echo "  make run          - 启动应用"
	@echo ""
	@echo "组合命令:"
	@echo "  make all          - 完整流程 (fix + test + run)"

# 安装生产依赖
install:
	uv pip install -e .

# 安装开发依赖
dev:
	uv pip install -e ".[dev]"

# 清理缓存和临时文件
clean:
	@echo "🧹 清理缓存文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ 清理完成"

# Ruff 检查 (不修复)
lint:
	@echo "📝 运行 Ruff 检查..."
	ruff check .

# Ruff 检查并自动修复
lint-fix:
	@echo "📝 运行 Ruff 检查并修复..."
	ruff check --fix .

# 格式化代码
format:
	@echo "🎨 格式化代码..."
	ruff format .

# 检查代码格式 (不修改)
format-check:
	@echo "🎨 检查代码格式..."
	ruff format --check .

# 完整检查 (CI 使用)
check: lint format-check
	@echo "✅ 代码检查通过"

# 完整修复 (开发使用)
fix: lint-fix format
	@echo "✅ 代码修复完成"

# 运行测试
test:
	@echo "🧪 运行测试..."
	uv run pytest

# 运行测试并生成覆盖率报告
test-cov:
	@echo "🧪 运行测试并生成覆盖率..."
	uv run pytest --cov=src --cov-report=html --cov-report=term
	@echo "📊 覆盖率报告: htmlcov/index.html"

# 启动应用
run:
	@echo "🚀 启动应用..."
	uv run python main.py

# 完整流程: 修复 -> 测试 -> 运行
all: fix test run
