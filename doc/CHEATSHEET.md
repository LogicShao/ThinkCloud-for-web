# UV + Ruff 快速参考

> 最常用命令速查表 - 打印出来贴在显示器旁边! 📌

---

## ⚡ 最常用命令 (TOP 10)

```bash
# 1. 安装/更新依赖
uv pip install -e ".[dev]"

# 2. 修复代码问题
ruff check --fix .

# 3. 格式化代码
ruff format .

# 4. 完整修复 (推荐)
ruff check --fix . && ruff format .

# 5. 运行应用
uv run python main.py

# 6. 运行测试
uv run pytest

# 7. 检查代码 (CI 使用)
ruff check .

# 8. 检查格式 (CI 使用)
ruff format --check .

# 9. 添加新包
uv pip install <package>

# 10. 导出依赖列表
uv pip freeze > requirements.txt
```

---

## 🔄 工作流速查

### 开始工作

```bash
git pull
uv pip install -e ".[dev]"
```

### 提交前

```bash
ruff check --fix . && ruff format .
uv run pytest
git add . && git commit -m "..."
```

### CI/CD

```bash
ruff check .
ruff format --check .
uv run pytest
```

---

## 🛠️ Makefile 快捷键 (如果你创建了 Makefile)

```bash
make dev          # 安装开发依赖
make fix          # 修复代码问题
make test         # 运行测试
make run          # 启动应用
make all          # 完整流程
```

---

## 🎯 VS Code 快捷键

| 操作     | Windows/Linux | macOS       |
|--------|---------------|-------------|
| 格式化文档  | Shift+Alt+F   | Shift+Opt+F |
| 快速修复   | Ctrl+.        | Cmd+.       |
| 运行任务   | Ctrl+Shift+B  | Cmd+Shift+B |
| 打开命令面板 | Ctrl+Shift+P  | Cmd+Shift+P |

然后输入 "Tasks: Run Task" 选择任务

---

## 🚨 常见错误处理

### 端口被占用

```bash
# 应用会自动查找可用端口 7860-7959
# 无需手动处理
```

### 依赖冲突

```bash
# 删除虚拟环境重新安装
rm -rf .venv          # Linux/Mac
Remove-Item -Recurse -Force .venv  # Windows
uv venv
uv pip install -e ".[dev]"
```

### Ruff 规则太严格

```python
# 在代码中忽略特定行
# ruff: noqa

# 或忽略特定规则
# ruff: noqa: E501
```

---

## 📝 注释语法

```python
# 忽略整个文件
# ruff: noqa

# 忽略整行
x = very_long_line()  # ruff: noqa

# 忽略特定规则
x = very_long_line()  # ruff: noqa: E501

# 忽略多个规则
x = very_long_line()  # ruff: noqa: E501, F401
```

---

## 🔧 配置位置

- **项目配置**: `pyproject.toml`
- **VS Code**: `.vscode/settings.json`
- **环境变量**: `.env`
- **Git 忽略**: `.gitignore`

---

## 📊 性能参考

| 操作              | 时间     | 对比         |
|-----------------|--------|------------|
| uv 安装 50 包      | ~3s    | pip: 30s   |
| ruff 检查 100 文件  | ~0.1s  | flake8: 5s |
| ruff 格式化 100 文件 | ~0.05s | black: 3s  |

---

## 🆘 获取帮助

```bash
# UV 帮助
uv --help
uv pip --help

# Ruff 帮助
ruff --help
ruff check --help
ruff format --help

# 查看规则
ruff rule E501
```

---

## 🌐 资源链接

- [UV 文档](https://docs.astral.sh/uv/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [Ruff 规则](https://docs.astral.sh/ruff/rules/)
- [项目详细指南](./UV_RUFF_GUIDE.md)

---

**打印提示**: 使用单色打印即可,重点命令已用符号标记 ⚡
