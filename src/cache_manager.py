"""
高级缓存管理器 - 支持多层缓存、LRU淘汰、持久化
"""

import hashlib
import json
import pickle
import threading
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0  # 估算的字节大小

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def touch(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheStats:
    """缓存统计信息"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size_bytes = 0
        self.total_entries = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_size_bytes": self.total_size_bytes,
            "total_entries": self.total_entries,
            "hit_rate": f"{self.hit_rate:.2%}",
        }


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        """
        初始化LRU缓存

        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存占用(MB)
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None

            entry = self.cache[key]

            # 检查是否过期
            if entry.is_expired():
                del self.cache[key]
                self.stats.total_entries -= 1
                self.stats.total_size_bytes -= entry.size_bytes
                self.stats.misses += 1
                return None

            # 更新访问信息
            entry.touch()

            # 移到末尾(最近使用)
            self.cache.move_to_end(key)

            self.stats.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 键
            value: 值
            ttl: 过期时间

        Returns:
            bool: 是否成功
        """
        with self.lock:
            # 估算值的大小
            size_bytes = self._estimate_size(value)

            # 检查单个值是否超出最大内存限制
            if size_bytes > self.max_memory_bytes:
                return False

            # 计算过期时间
            expires_at = datetime.now() + ttl if ttl else None

            # 如果键已存在,先移除旧值
            if key in self.cache:
                old_entry = self.cache[key]
                self.stats.total_size_bytes -= old_entry.size_bytes
                self.stats.total_entries -= 1
                del self.cache[key]

            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            # 淘汰旧条目直到满足大小和内存限制
            while (
                len(self.cache) >= self.max_size
                or (self.stats.total_size_bytes + size_bytes) > self.max_memory_bytes
            ):
                if not self.cache:
                    break
                self._evict_oldest()

            # 添加新条目
            self.cache[key] = entry
            self.stats.total_entries += 1
            self.stats.total_size_bytes += size_bytes

            return True

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.stats.total_entries -= 1
                self.stats.total_size_bytes -= entry.size_bytes
                del self.cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.stats.total_entries = 0
            self.stats.total_size_bytes = 0

    def _evict_oldest(self):
        """淘汰最旧的条目"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.stats.total_entries -= 1
            self.stats.total_size_bytes -= entry.size_bytes
            self.stats.evictions += 1

    def _estimate_size(self, value: Any) -> int:
        """估算对象大小(字节)"""
        try:
            # 尝试序列化估算大小
            return len(pickle.dumps(value))
        except Exception:
            # 如果无法序列化,使用粗略估算
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v) for k, v in value.items()
                )
            else:
                return 100  # 默认值

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            return self.stats.to_dict()


class CacheManager:
    """
    高级缓存管理器
    支持多层缓存、持久化、过期策略
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl: Optional[timedelta] = None,
        enable_persistence: bool = False,
        persistence_path: Optional[Path] = None,
    ):
        """
        初始化缓存管理器

        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存占用(MB)
            default_ttl: 默认过期时间
            enable_persistence: 是否启用持久化
            persistence_path: 持久化文件路径
        """
        self.lru_cache = LRUCache(max_size=max_size, max_memory_mb=max_memory_mb)
        self.default_ttl = default_ttl or timedelta(minutes=10)
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path or Path(".cache/api_cache.pkl")

        # 加载持久化缓存
        if self.enable_persistence:
            self._load_from_disk()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值,不存在或过期返回None
        """
        return self.lru_cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间,None使用默认值

        Returns:
            bool: 是否成功
        """
        ttl = ttl if ttl is not None else self.default_ttl
        success = self.lru_cache.set(key, value, ttl)

        # 持久化
        if success and self.enable_persistence:
            self._save_to_disk()

        return success

    def get_or_compute(
        self, key: str, compute_fn: Callable[[], Any], ttl: Optional[timedelta] = None
    ) -> Any:
        """
        获取缓存值,如果不存在则计算并缓存

        Args:
            key: 缓存键
            compute_fn: 计算函数
            ttl: 过期时间

        Returns:
            Any: 缓存值或计算结果
        """
        # 尝试从缓存获取
        value = self.get(key)
        if value is not None:
            return value

        # 计算新值
        value = compute_fn()

        # 缓存结果
        self.set(key, value, ttl)

        return value

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功
        """
        success = self.lru_cache.delete(key)

        # 持久化
        if success and self.enable_persistence:
            self._save_to_disk()

        return success

    def clear(self):
        """清空所有缓存"""
        self.lru_cache.clear()

        # 删除持久化文件
        if self.enable_persistence and self.persistence_path.exists():
            self.persistence_path.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.lru_cache.get_stats()

    def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            int: 清理的条目数
        """
        with self.lru_cache.lock:
            expired_keys = []
            for key, entry in self.lru_cache.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                self.lru_cache.delete(key)

            if expired_keys and self.enable_persistence:
                self._save_to_disk()

            return len(expired_keys)

    def _save_to_disk(self):
        """保存缓存到磁盘"""
        try:
            # 确保目录存在
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

            # 序列化缓存
            with open(self.persistence_path, "wb") as f:
                # 只保存未过期的条目
                valid_cache = OrderedDict()
                with self.lru_cache.lock:
                    for key, entry in self.lru_cache.cache.items():
                        if not entry.is_expired():
                            valid_cache[key] = entry

                pickle.dump(valid_cache, f)

        except Exception as e:
            print(f"[CACHE] 保存缓存到磁盘失败: {e}")

    def _load_from_disk(self):
        """从磁盘加载缓存"""
        try:
            if not self.persistence_path.exists():
                return

            with open(self.persistence_path, "rb") as f:
                loaded_cache = pickle.load(f)

            # 加载到LRU缓存
            with self.lru_cache.lock:
                for key, entry in loaded_cache.items():
                    if not entry.is_expired():
                        self.lru_cache.cache[key] = entry
                        self.lru_cache.stats.total_entries += 1
                        self.lru_cache.stats.total_size_bytes += entry.size_bytes

            print(f"[CACHE] 从磁盘加载了 {len(loaded_cache)} 个缓存条目")

        except Exception as e:
            print(f"[CACHE] 从磁盘加载缓存失败: {e}")


def generate_cache_key(prefix: str, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 键前缀
        **kwargs: 键值对

    Returns:
        str: 缓存键
    """
    # 排序并序列化参数
    sorted_params = sorted(kwargs.items())
    params_str = json.dumps(sorted_params, sort_keys=True)

    # 生成哈希
    hash_value = hashlib.md5(params_str.encode()).hexdigest()

    return f"{prefix}:{hash_value}"


# 全局缓存管理器实例
# 响应缓存 - 用于API响应
response_cache = CacheManager(
    max_size=500,
    max_memory_mb=50,
    default_ttl=timedelta(minutes=10),
    enable_persistence=True,
    persistence_path=Path(".cache/response_cache.pkl"),
)

# 会话缓存 - 用于会话状态
session_cache = CacheManager(
    max_size=100, max_memory_mb=20, default_ttl=timedelta(hours=24), enable_persistence=True, persistence_path=Path(".cache/session_cache.pkl")
)

# 配置缓存 - 用于模型配置
config_cache = CacheManager(
    max_size=50, max_memory_mb=5, default_ttl=timedelta(days=1), enable_persistence=True, persistence_path=Path(".cache/config_cache.pkl")
)
