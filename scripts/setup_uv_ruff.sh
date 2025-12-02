#!/bin/bash
# SimpleLLMFront - UV + Ruff 快速设置脚本
# 运行方式: bash setup_uv_ruff.sh

set -e

echo "=================================="
echo "SimpleLLMFront UV + Ruff 设置向导"
echo "=================================="
echo ""

# 检查 uv 是否已安装
echo "1️⃣  检查 uv 是否已安装..."
if command -v uv &> /dev/null; then
    echo "   ✅ uv 已安装"
else
    echo "   ⚠️  uv 未安装。正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 重新加载 PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo "   ✅ uv 安装成功!"
fi

# 检查 ruff 是否已安装
echo ""
echo "2️⃣  检查 ruff 是否已安装..."
if command -v ruff &> /dev/null; then
    echo "   ✅ ruff 已安装"
else
    echo "   ⚠️  ruff 未安装。正在通过 uv 安装..."
    uv tool install ruff
    echo "   ✅ ruff 安装成功!"
fi

# 询问用户是否创建新环境
echo ""
echo "3️⃣  虚拟环境配置"
read -p "   是否重新创建虚拟环境? (会删除现有 .venv) [y/N]: " recreate_venv

if [[ "$recreate_venv" =~ ^[Yy]$ ]]; then
    echo "   🗑️  删除现有虚拟环境..."
    rm -rf .venv

    echo "   🔨 创建新虚拟环境..."
    uv venv
    echo "   ✅ 虚拟环境创建完成"
fi

# 安装依赖
echo ""
echo "4️⃣  安装项目依赖..."
uv pip install -e ".[dev]"
echo "   ✅ 依赖安装成功!"

# 运行 ruff 检查
echo ""
echo "5️⃣  运行代码质量检查..."
echo "   📝 Ruff Linting..."
ruff check . --fix

echo "   🎨 Ruff Formatting..."
ruff format .

echo "   ✅ 代码检查完成!"

# 完成
echo ""
echo "================================"
echo "✨ 设置完成!"
echo "================================"
echo ""
echo "下一步:"
echo "  1. 激活虚拟环境: source .venv/bin/activate"
echo "  2. 运行应用: python main.py"
echo "  3. 或直接运行: uv run python main.py"
echo ""
echo "常用命令:"
echo "  - 代码检查: ruff check ."
echo "  - 代码格式化: ruff format ."
echo "  - 运行测试: uv run pytest"
echo ""
echo "📖 详细文档请查看: UV_RUFF_GUIDE.md"
