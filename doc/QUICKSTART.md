# SimpleLLMFront - UV + Ruff 快速开始

## 方式一: 自动化脚本 (推荐)

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_uv_ruff.ps1
```

### Linux/macOS

```bash
chmod +x scripts/setup_uv_ruff.sh
./scripts/setup_uv_ruff.sh
```

---

## 方式二: 手动操作 (3 步)

### 步骤 1: 安装工具

**Windows:**

```powershell
# 安装 uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 ruff
pip install ruff
```

**Linux/macOS:**

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 ruff
pip install ruff
```

### 步骤 2: 安装依赖

```bash
# 安装项目依赖 (含开发工具)
uv pip install -e ".[dev]"
```

### 步骤 3: 验证安装

```bash
# 检查代码
ruff check .

# 格式化代码
ruff format .

# 运行测试
uv run pytest

# 启动应用
uv run python main.py
```

---

## 日常使用

### 每天开始工作

```bash
git pull
uv pip install -e ".[dev]"
```

### 提交代码前

```bash
# 自动修复并格式化
ruff check --fix . && ruff format .

# 运行测试
uv run pytest

# 提交
git add .
git commit -m "your message"
```

### 使用 Makefile (如果你的系统支持)

```bash
make dev      # 安装开发依赖
make fix      # 修复代码
make test     # 运行测试
make run      # 启动应用
make all      # 完整流程
```

---

## VS Code 集成

1. 安装推荐的扩展 (打开项目时会自动提示):
    - Ruff (官方)
    - Python (Microsoft)

2. 配置已自动完成 (.vscode/settings.json):
    - ✅ 保存时自动格式化
    - ✅ 保存时自动修复问题
    - ✅ 自动排序 imports

3. 使用任务快捷键:
    - `Ctrl+Shift+B` (Windows/Linux) 或 `Cmd+Shift+B` (macOS)
    - 选择要运行的任务

---

## 📚 完整文档

- **详细指南**: `UV_RUFF_GUIDE.md`
- **快速参考**: `CHEATSHEET.md`
- **项目说明**: `CLAUDE.md`

---

## ⚡ Top 5 命令

```bash
1. uv pip install -e ".[dev]"           # 安装依赖
2. ruff check --fix . && ruff format .  # 修复代码
3. uv run python main.py                # 运行应用
4. uv run pytest                        # 运行测试
5. make all                             # 完整流程 (如果支持)
```

---

现在开始享受极速的 Python 开发体验! 🚀
