"""
深度思考工具函数
包含JSON解析器、缓存管理器等工具类
"""

import hashlib
import json
import threading
from typing import Any, Dict

from .core.interfaces import ICacheManager, IJSONParser


class DefaultJSONParser(IJSONParser):
    """默认JSON解析器，支持容错处理"""

    def parse(self, response: str) -> Dict[str, Any]:
        """解析JSON响应，支持容错处理"""
        # 防护：如果收到生成器对象，将其转换为字符串
        if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
            try:
                response = ''.join(response)
            except Exception as e:
                raise TypeError(f"响应必须是字符串，而不是 {type(response).__name__}: {e}")

        # 确保是字符串类型
        if not isinstance(response, str):
            raise TypeError(f"响应必须是字符串，而不是 {type(response).__name__}")

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON代码块
        if "```json" in response:
            json_block = response.split("```json")[1].split("```")[0].strip()
            try:
                return json.loads(json_block)
            except json.JSONDecodeError:
                pass

        # 尝试查找花括号内的内容
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

        # 如果都失败，抛出异常
        raise ValueError(f"无法解析JSON响应: {response[:100]}...")


class MemoryCacheManager(ICacheManager):
    """内存缓存管理器"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """获取缓存值"""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            self._cache[key] = value

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


def generate_cache_key(method_name: str, *args, **kwargs) -> str:
    """生成缓存键"""
    cache_input = {
        "method": method_name,
        "args": args,
        "kwargs": {k: v for k, v in kwargs.items() if k != "self"},
    }
    cache_str = str(sorted(cache_input.items()))
    return hashlib.md5(cache_str.encode()).hexdigest()
