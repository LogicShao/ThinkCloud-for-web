# UV + Ruff 使用指南

> SimpleLLMFront 项目的现代 Python 工具链指南

---

## 📥 安装工具

### Windows (PowerShell)

```powershell
# 安装 uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 ruff
pip install ruff
# 或使用 uv 全局安装
uv tool install ruff
```

### macOS/Linux

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 ruff
pip install ruff
# 或使用 uv 全局安装
uv tool install ruff
```

---

## 🔄 从 requirements.txt 迁移

### 方案一: 保留现有虚拟环境 (推荐快速开始)

```bash
# 1. 使用 uv 同步依赖到现有 .venv
uv pip sync requirements.txt

# 2. 安装开发依赖
uv pip install -e ".[dev]"
```

### 方案二: 全新环境 (推荐长期使用)

```bash
# 1. 删除旧虚拟环境 (可选)
# rm -rf .venv  # Linux/Mac
# Remove-Item -Recurse -Force .venv  # Windows

# 2. 使用 uv 创建新虚拟环境并安装依赖
uv venv
uv pip install -e ".[dev]"

# 3. (可选) 生成 uv.lock 锁文件
uv lock
```

---

## 💻 日常开发命令

### 依赖管理

```bash
# 安装项目依赖 (生产环境)
uv pip install -e .

# 安装项目依赖 (含开发工具)
uv pip install -e ".[dev]"

# 添加新依赖
uv pip install <package>
# 然后手动更新 pyproject.toml 的 dependencies 列表

# 导出 requirements.txt (用于兼容性)
uv pip freeze > requirements.txt

# 更新所有依赖到最新版本
uv pip install --upgrade -e ".[dev]"
```

### 代码质量检查

```bash
# 1️⃣ Linting (检查代码问题)
ruff check .                    # 检查所有文件
ruff check src/                 # 仅检查 src 目录
ruff check main.py              # 检查单个文件
ruff check --fix .              # 自动修复可修复的问题

# 2️⃣ Formatting (格式化代码)
ruff format .                   # 格式化所有文件
ruff format src/                # 仅格式化 src 目录
ruff format --check .           # 仅检查格式(不修改)
ruff format --diff .            # 显示格式差异

# 3️⃣ 组合命令 (推荐工作流)
ruff check --fix . && ruff format .  # 先修复问题,再格式化
```

### 运行应用

```bash
# 使用 uv 运行 (无需激活虚拟环境)
uv run python main.py

# 或者激活虚拟环境后运行
# Windows
.venv\Scripts\activate
python main.py

# Linux/Mac
source .venv/bin/activate
python main.py
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_ui.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 查看覆盖率报告
# 浏览器打开 htmlcov/index.html
```

---

## ⚙️ 配置说明

### pyproject.toml 结构

```toml
[project]
# 项目元数据
name = "SimpleLLMFront"
dependencies = [...]          # 生产依赖

[project.optional-dependencies]
dev = [...]                   # 开发依赖

[tool.ruff]
# Ruff 全局配置
line-length = 100             # 每行最大字符数
target-version = "py38"       # 目标 Python 版本

[tool.ruff.lint]
select = ["E", "F", "I", ...]  # 启用的规则
ignore = ["E501", ...]         # 忽略的规则

[tool.ruff.format]
# 格式化配置
quote-style = "double"        # 双引号
```

### Ruff 规则说明

| 规则组 | 说明                  | 示例             |
|-----|---------------------|----------------|
| E/W | PEP 8 风格检查          | 缩进、空格、换行       |
| F   | Pyflakes (逻辑错误)     | 未使用变量、重复导入     |
| I   | Import 排序           | 导入语句自动分组排序     |
| N   | 命名规范                | 变量/函数/类命名检查    |
| UP  | Python 语法现代化        | 使用新语法替代旧语法     |
| B   | 常见错误模式              | 可变默认参数、函数副作用   |
| C4  | 列表/字典推导式优化          | 简化推导式表达式       |
| SIM | 代码简化                | 简化 if/for 等逻辑  |
| RUF | Ruff 特定规则 (性能/最佳实践) | 各种 Python 最佳实践 |

---

## 🔧 IDE 集成

### VS Code

1. 安装扩展:
    - `Ruff` (官方扩展)
    - `Python` (Microsoft)

2. 配置 `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.lint.enable": true,
  "ruff.format.enable": true
}
```

### PyCharm / IntelliJ IDEA

1. 安装插件: `Ruff`
2. Settings → Tools → Ruff
    - ✅ Enable Ruff
    - ✅ Run ruff on save
    - ✅ Use ruff format

---

## 📊 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Lint and Test

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          uv venv
          uv pip install -e ".[dev]"

      - name: Ruff check
        run: ruff check .

      - name: Ruff format check
        run: ruff format --check .

      - name: Run tests
        run: uv run pytest
```

---

## 🎯 日常工作流

### 开发新功能

```bash
# 1. 拉取最新代码
git pull

# 2. 安装/更新依赖
uv pip install -e ".[dev]"

# 3. 开发代码...

# 4. 运行检查
ruff check --fix .
ruff format .

# 5. 运行测试
uv run pytest

# 6. 提交代码
git add .
git commit -m "feat: 新功能"
git push
```

### Pre-commit 钩子 (可选)

```bash
# 安装 pre-commit
uv pip install pre-commit

# 创建 .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
EOF

# 安装钩子
pre-commit install

# 现在每次 git commit 会自动运行 ruff
```

---

## ⚡ 性能对比

| 工具         | 操作          | 传统工具 (pip)    | uv      | 提升  |
|------------|-------------|---------------|---------|-----|
| 依赖安装       | 安装 50 个包    | ~30 秒         | ~3 秒    | 10x |
| 环境创建       | 创建虚拟环境      | ~5 秒          | ~0.5 秒  | 10x |
| Linting    | 检查 100 个文件  | ~5 秒 (flake8) | ~0.1 秒  | 50x |
| Formatting | 格式化 100 个文件 | ~3 秒 (black)  | ~0.05 秒 | 60x |

---

## 🆚 与传统工具对比

| 传统工具                                    | UV + Ruff 替代方案                             |
|-----------------------------------------|--------------------------------------------|
| `pip install`                           | `uv pip install`                           |
| `pip install -r requirements.txt`       | `uv pip sync requirements.txt`             |
| `python -m venv .venv`                  | `uv venv`                                  |
| `black .`                               | `ruff format .`                            |
| `flake8 .`                              | `ruff check .`                             |
| `isort .`                               | `ruff check --select I --fix .` (已包含在默认配置) |
| `pylint` + `flake8` + `black` + `isort` | `ruff` (统一工具)                              |

---

## ❓ 常见问题

### Q: 是否必须删除 requirements.txt?

A: 不必须。可以两者共存:

- `pyproject.toml`: 主要依赖声明
- `requirements.txt`: 精确版本锁定 (通过 `uv pip freeze` 生成)

### Q: uv 和 pip 可以混用吗?

A: 可以,但不推荐。建议统一使用 `uv pip` 命令。

### Q: 如何调整 Ruff 规则?

A: 编辑 `pyproject.toml` 的 `[tool.ruff.lint]` 部分:

```toml
[tool.ruff.lint]
ignore = ["E501"]  # 添加要忽略的规则
```

### Q: 某段代码需要忽略 Ruff 检查?

A: 使用注释:

```python
# ruff: noqa         # 忽略整行
# ruff: noqa: E501   # 忽略特定规则
```

---

## 📚 参考资料

- [uv 官方文档](https://docs.astral.sh/uv/)
- [Ruff 官方文档](https://docs.astral.sh/ruff/)
- [Ruff 规则列表](https://docs.astral.sh/ruff/rules/)
- [pyproject.toml 规范](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

---

**维护者**: 根据项目需求持续更新本文档
**最后更新**: 2025-12-02
