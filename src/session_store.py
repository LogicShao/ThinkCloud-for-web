"""
会话状态持久化 - 支持对话历史、模型配置、UI状态的保存和恢复
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache_manager import session_cache


@dataclass
class ModelConfig:
    """模型配置"""

    provider: str
    model: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_instruction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """从字典创建"""
        return cls(**data)


@dataclass
class DeepThinkConfig:
    """深度思考配置"""

    enabled: bool = False
    max_tasks: int = 6
    enable_review: bool = True
    enable_web_search: bool = False
    show_process: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeepThinkConfig":
        """从字典创建"""
        return cls(**data)


@dataclass
class ChatMessage:
    """对话消息"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """从字典创建"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionState:
    """会话状态"""

    session_id: str
    created_at: datetime
    updated_at: datetime
    chat_history: List[ChatMessage] = field(default_factory=list)
    model_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(provider="cerebras", model="llama-3.3-70b")
    )
    deep_think_config: DeepThinkConfig = field(default_factory=DeepThinkConfig)
    ui_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "chat_history": [msg.to_dict() for msg in self.chat_history],
            "model_config": self.model_config.to_dict(),
            "deep_think_config": self.deep_think_config.to_dict(),
            "ui_state": self.ui_state,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """从字典创建"""
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            chat_history=[ChatMessage.from_dict(msg) for msg in data.get("chat_history", [])],
            model_config=ModelConfig.from_dict(data.get("model_config", {})),
            deep_think_config=DeepThinkConfig.from_dict(data.get("deep_think_config", {})),
            ui_state=data.get("ui_state", {}),
        )


class SessionStore:
    """
    会话存储管理器
    支持会话的创建、保存、加载、删除
    """

    def __init__(self, storage_path: Optional[Path] = None, enable_disk_persistence: bool = True):
        """
        初始化会话存储

        Args:
            storage_path: 磁盘存储路径
            enable_disk_persistence: 是否启用磁盘持久化
        """
        self.storage_path = storage_path or Path(".sessions")
        self.enable_disk_persistence = enable_disk_persistence

        # 确保存储目录存在
        if self.enable_disk_persistence:
            self.storage_path.mkdir(parents=True, exist_ok=True)

        # 当前活动会话
        self.current_session: Optional[SessionState] = None

    def create_session(self) -> SessionState:
        """
        创建新会话

        Returns:
            SessionState: 新会话状态
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()

        session = SessionState(session_id=session_id, created_at=now, updated_at=now)

        self.current_session = session

        # 保存到缓存
        session_cache.set(session_id, session)

        # 保存到磁盘
        if self.enable_disk_persistence:
            self._save_to_disk(session)

        print(f"[SESSION] 创建新会话: {session_id}")
        return session

    def save_session(self, session: SessionState):
        """
        保存会话状态

        Args:
            session: 会话状态
        """
        session.updated_at = datetime.now()

        # 保存到缓存
        session_cache.set(session.session_id, session)

        # 保存到磁盘
        if self.enable_disk_persistence:
            self._save_to_disk(session)

    def load_session(self, session_id: str) -> Optional[SessionState]:
        """
        加载会话状态

        Args:
            session_id: 会话ID

        Returns:
            SessionState: 会话状态,不存在返回None
        """
        # 先从缓存加载
        session = session_cache.get(session_id)
        if session:
            print(f"[SESSION] 从缓存加载会话: {session_id}")
            self.current_session = session
            return session

        # 从磁盘加载
        if self.enable_disk_persistence:
            session = self._load_from_disk(session_id)
            if session:
                print(f"[SESSION] 从磁盘加载会话: {session_id}")
                # 加载到缓存
                session_cache.set(session_id, session)
                self.current_session = session
                return session

        print(f"[SESSION] 会话不存在: {session_id}")
        return None

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        # 从缓存删除
        session_cache.delete(session_id)

        # 从磁盘删除
        if self.enable_disk_persistence:
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()

        # 如果是当前会话,清空
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session = None

        print(f"[SESSION] 删除会话: {session_id}")
        return True

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话

        Returns:
            List[Dict]: 会话信息列表
        """
        sessions = []

        if not self.enable_disk_persistence:
            return sessions

        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data["session_id"],
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"],
                            "message_count": len(data.get("chat_history", [])),
                        }
                    )
            except Exception as e:
                print(f"[SESSION] 读取会话文件失败 {session_file}: {e}")

        # 按更新时间倒序排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)

        return sessions

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState:
        """
        获取或创建会话

        Args:
            session_id: 会话ID,None则创建新会话

        Returns:
            SessionState: 会话状态
        """
        if session_id:
            session = self.load_session(session_id)
            if session:
                return session

        return self.create_session()

    def update_chat_history(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        更新对话历史

        Args:
            role: 角色
            content: 内容
            metadata: 元数据
        """
        if not self.current_session:
            self.create_session()

        message = ChatMessage(role=role, content=content, metadata=metadata or {})

        self.current_session.chat_history.append(message)
        self.save_session(self.current_session)

    def update_model_config(self, config: ModelConfig):
        """
        更新模型配置

        Args:
            config: 模型配置
        """
        if not self.current_session:
            self.create_session()

        self.current_session.model_config = config
        self.save_session(self.current_session)

    def update_deep_think_config(self, config: DeepThinkConfig):
        """
        更新深度思考配置

        Args:
            config: 深度思考配置
        """
        if not self.current_session:
            self.create_session()

        self.current_session.deep_think_config = config
        self.save_session(self.current_session)

    def update_ui_state(self, ui_state: Dict[str, Any]):
        """
        更新UI状态

        Args:
            ui_state: UI状态
        """
        if not self.current_session:
            self.create_session()

        self.current_session.ui_state.update(ui_state)
        self.save_session(self.current_session)

    def clear_chat_history(self):
        """清空对话历史"""
        if self.current_session:
            self.current_session.chat_history.clear()
            self.save_session(self.current_session)

    def export_session(self, session_id: str, export_path: Path) -> bool:
        """
        导出会话到文件

        Args:
            session_id: 会话ID
            export_path: 导出路径

        Returns:
            bool: 是否成功
        """
        session = self.load_session(session_id)
        if not session:
            return False

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"[SESSION] 导出会话到: {export_path}")
            return True
        except Exception as e:
            print(f"[SESSION] 导出会话失败: {e}")
            return False

    def import_session(self, import_path: Path) -> Optional[SessionState]:
        """
        从文件导入会话

        Args:
            import_path: 导入路径

        Returns:
            SessionState: 会话状态,失败返回None
        """
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            session = SessionState.from_dict(data)

            # 保存到缓存和磁盘
            session_cache.set(session.session_id, session)
            if self.enable_disk_persistence:
                self._save_to_disk(session)

            print(f"[SESSION] 导入会话: {session.session_id}")
            return session

        except Exception as e:
            print(f"[SESSION] 导入会话失败: {e}")
            return None

    def _save_to_disk(self, session: SessionState):
        """保存会话到磁盘"""
        try:
            session_file = self.storage_path / f"{session.session_id}.json"
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SESSION] 保存会话到磁盘失败: {e}")

    def _load_from_disk(self, session_id: str) -> Optional[SessionState]:
        """从磁盘加载会话"""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            if not session_file.exists():
                return None

            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return SessionState.from_dict(data)

        except Exception as e:
            print(f"[SESSION] 从磁盘加载会话失败: {e}")
            return None


# 全局会话存储实例
session_store = SessionStore()
