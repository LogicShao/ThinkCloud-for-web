"""
阶段处理器基类
遵循开闭原则，支持扩展新的阶段处理器
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ..core.interfaces import ILLMService, IJSONParser, IStageProcessor
from ..core.models import StageContext, StageResult, ThinkingStage

logger = logging.getLogger(__name__)


class BaseStageProcessor(IStageProcessor):
    """阶段处理器基类"""

    def __init__(
            self,
            llm_service: ILLMService,
            json_parser: IJSONParser,
            verbose: bool = True,
    ):
        """
        初始化阶段处理器

        Args:
            llm_service: LLM服务实例
            json_parser: JSON解析器
            verbose: 是否输出详细日志
        """
        self.llm_service = llm_service
        self.json_parser = json_parser
        self.verbose = verbose
        self.logger = logger

    @abstractmethod
    def get_stage(self) -> ThinkingStage:
        """获取阶段类型"""
        pass

    @abstractmethod
    def execute(self, context: StageContext, **kwargs) -> StageResult:
        """执行阶段处理"""
        pass

    def _call_llm(
            self,
            prompt: str,
            context: StageContext,
            stage: ThinkingStage,
            system_instruction: Optional[str] = None,
    ) -> str:
        """调用LLM"""
        context.llm_call_count += 1

        if self.verbose:
            self.logger.info(f"[LLM CALL #{context.llm_call_count}] Stage: {stage.value}")

        messages = [{"role": "user", "content": prompt}]

        response = self.llm_service.chat_completion(
            messages=messages,
            model=context.model,
            system_instruction=system_instruction or context.system_instruction,
            temperature=context.temperature,
            top_p=context.top_p,
            max_tokens=context.max_tokens,
            stream=False,  # 深度思考模式必须使用非流式传输
        )

        # 确保返回的是字符串类型
        if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
            if self.verbose:
                self.logger.warning(f"[LLM CALL] 检测到生成器响应，类型: {type(response).__name__}")
            try:
                chunks = []
                for i, chunk in enumerate(response):
                    # 日志记录前几个chunk的类型和内容
                    if self.verbose and i < 3:
                        chunk_type = type(chunk).__name__
                        chunk_preview = str(chunk)[:100]
                        self.logger.debug(f"[LLM CALL] Chunk {i} 类型: {chunk_type}, 内容预览: {chunk_preview}")

                    # 尝试多种方式提取内容
                    if isinstance(chunk, str):
                        chunks.append(chunk)
                    elif hasattr(chunk, 'content'):
                        chunks.append(chunk.content if chunk.content else '')
                    elif hasattr(chunk, 'text'):
                        chunks.append(chunk.text if chunk.text else '')
                    elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                        chunks.append(chunk.delta.content if chunk.delta.content else '')
                    else:
                        chunks.append(str(chunk))

                response = ''.join(chunks)

                if self.verbose:
                    self.logger.info(f"[LLM CALL] 生成器转换完成，共{len(chunks)}个chunk，总长度: {len(response)}")
            except Exception as e:
                error_msg = f"无法将生成器转换为字符串: {e}"
                self.logger.error(f"[LLM CALL] {error_msg}")
                raise TypeError(error_msg)

        # 最终类型检查
        if not isinstance(response, str):
            raise TypeError(f"API 响应必须是字符串，而不是 {type(response).__name__}")

        # 调试日志：显示完整响应内容以方便JSON解析调试
        if self.verbose:
            self.logger.info(f"[LLM CALL] 最终响应类型: {type(response).__name__}, 长度: {len(response)}")

            # 为了便于日志查看，显示前500字符作为预览
            preview_length = 500
            if len(response) > 0:
                preview = response[:preview_length].replace('\n', ' ')
                self.logger.info(f"[LLM RESPONSE PREVIEW] {preview}{'...' if len(response) > preview_length else ''}")
            else:
                self.logger.warning("[LLM RESPONSE PREVIEW] 响应为空字符串！")

            # 同时记录完整响应到DEBUG级别日志（方便调试JSON解析问题，避免日志过长）
            if len(response) > 0:
                self.logger.debug(f"[LLM RESPONSE FULL] {response}")
            else:
                self.logger.error("[LLM RESPONSE FULL] 响应为空！这可能导致JSON解析失败")
        return response

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        return self.json_parser.parse(response)

    def _create_success_result(self, data: Any, llm_calls: int = 1) -> StageResult:
        """创建成功结果"""
        return StageResult(
            stage=self.get_stage(),
            success=True,
            data=data,
            llm_calls=llm_calls,
        )

    def _create_error_result(self, error: str, llm_calls: int = 0) -> StageResult:
        """创建错误结果"""
        return StageResult(
            stage=self.get_stage(),
            success=False,
            data=None,
            error=error,
            llm_calls=llm_calls,
        )
