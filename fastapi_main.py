"""
FastAPI 服务启动脚本

运行方式：
    python fastapi_main.py

或使用 uvicorn 直接启动：
    uvicorn src.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import uvicorn
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """启动 FastAPI 服务"""
    # 配置服务器
    config = {
        "app": "src.fastapi_server:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,  # 开发模式：自动重载
        "log_level": "info",
        "access_log": True,
    }

    print("\n" + "=" * 60)
    print("🌟 启动 ThinkCloud FastAPI 服务...")
    print("=" * 60)
    print(f"📍 地址: http://localhost:{config['port']}")
    print(f"📖 API 文档: http://localhost:{config['port']}/docs")
    print(f"📋 ReDoc 文档: http://localhost:{config['port']}/redoc")
    print(f"🔧 开发模式: {'启用' if config['reload'] else '禁用'}")
    print("=" * 60 + "\n")

    # 启动服务器
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
