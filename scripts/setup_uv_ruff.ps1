# SimpleLLMFront - UV + Ruff 快速设置脚本
# 运行方式: powershell -ExecutionPolicy Bypass -File setup_uv_ruff.ps1

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "SimpleLLMFront UV + Ruff 设置向导" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 检查 uv 是否已安装
Write-Host "1️⃣  检查 uv 是否已安装..." -ForegroundColor Yellow
$uvInstalled = $null -ne (Get-Command "uv" -ErrorAction SilentlyContinue)

if (-not $uvInstalled) {
    Write-Host "   ⚠️  uv 未安装。正在安装..." -ForegroundColor Red
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        Write-Host "   ✅ uv 安装成功!" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ uv 安装失败: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ uv 已安装" -ForegroundColor Green
}

# 检查 ruff 是否已安装
Write-Host ""
Write-Host "2️⃣  检查 ruff 是否已安装..." -ForegroundColor Yellow
$ruffInstalled = $null -ne (Get-Command "ruff" -ErrorAction SilentlyContinue)

if (-not $ruffInstalled) {
    Write-Host "   ⚠️  ruff 未安装。正在通过 uv 安装..." -ForegroundColor Red
    try {
        uv tool install ruff
        Write-Host "   ✅ ruff 安装成功!" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ ruff 安装失败: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ ruff 已安装" -ForegroundColor Green
}

# 询问用户是否创建新环境
Write-Host ""
Write-Host "3️⃣  虚拟环境配置" -ForegroundColor Yellow
$recreateVenv = Read-Host "   是否重新创建虚拟环境? (会删除现有 .venv) [y/N]"

if ($recreateVenv -eq "y" -or $recreateVenv -eq "Y") {
    Write-Host "   🗑️  删除现有虚拟环境..." -ForegroundColor Red
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force .venv
    }

    Write-Host "   🔨 创建新虚拟环境..." -ForegroundColor Yellow
    uv venv
    Write-Host "   ✅ 虚拟环境创建完成" -ForegroundColor Green
}

# 安装依赖
Write-Host ""
Write-Host "4️⃣  安装项目依赖..." -ForegroundColor Yellow
try {
    uv pip install -e ".[dev]"
    Write-Host "   ✅ 依赖安装成功!" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 依赖安装失败: $_" -ForegroundColor Red
    exit 1
}

# 运行 ruff 检查
Write-Host ""
Write-Host "5️⃣  运行代码质量检查..." -ForegroundColor Yellow
Write-Host "   📝 Ruff Linting..." -ForegroundColor Cyan
ruff check . --fix

Write-Host "   🎨 Ruff Formatting..." -ForegroundColor Cyan
ruff format .

Write-Host "   ✅ 代码检查完成!" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✨ 设置完成!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 激活虚拟环境: .venv\Scripts\activate" -ForegroundColor White
Write-Host "  2. 运行应用: python main.py" -ForegroundColor White
Write-Host "  3. 或直接运行: uv run python main.py" -ForegroundColor White
Write-Host ""
Write-Host "常用命令:" -ForegroundColor Yellow
Write-Host "  - 代码检查: ruff check ." -ForegroundColor White
Write-Host "  - 代码格式化: ruff format ." -ForegroundColor White
Write-Host "  - 运行测试: uv run pytest" -ForegroundColor White
Write-Host ""
Write-Host "📖 详细文档请查看: UV_RUFF_GUIDE.md" -ForegroundColor Cyan
