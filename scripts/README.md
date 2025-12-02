# Scripts 目录

本目录包含项目的自动化脚本和工具。

## 脚本列表

### setup_uv_ruff.ps1

**用途**：Windows 环境下自动安装和配置 UV 和 Ruff 开发工具

**运行方式**：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_uv_ruff.ps1
```

**功能**：

- 自动检测并安装 UV（Python 包管理器）
- 自动检测并安装 Ruff（代码检查和格式化工具）
- 安装项目依赖（包括开发依赖）
- 验证安装结果

**适用系统**：Windows

---

### setup_uv_ruff.sh

**用途**：Linux/macOS 环境下自动安装和配置 UV 和 Ruff 开发工具

**运行方式**：

```bash
chmod +x scripts/setup_uv_ruff.sh
./scripts/setup_uv_ruff.sh
```

**功能**：

- 自动检测并安装 UV（Python 包管理器）
- 自动检测并安装 Ruff（代码检查和格式化工具）
- 安装项目依赖（包括开发依赖）
- 验证安装结果

**适用系统**：Linux, macOS

---

## 使用建议

1. **首次设置项目**：运行对应系统的 `setup_uv_ruff` 脚本，一键完成开发环境配置
2. **CI/CD 集成**：可以在 CI 流程中使用这些脚本自动化环境配置
3. **团队协作**：新成员加入项目时，运行脚本快速搭建开发环境

## 相关文档

- [快速开始指南](../doc/QUICKSTART.md)
- [UV & Ruff 详细指南](../doc/UV_RUFF_GUIDE.md)
- [速查表](../doc/CHEATSHEET.md)

---

## 注意事项

- 脚本会自动检测是否已安装工具，避免重复安装
- 如果遇到权限问题，请使用管理员权限运行
- 确保网络连接正常，脚本需要从互联网下载工具
