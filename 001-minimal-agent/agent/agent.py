"""
Agent 主类

提供用户友好的接口来与 AI Agent 交互。
"""

import os
import json
import time
from typing import List, Optional, Callable, Set

from agent.types import (
    AgentState,
    AgentConfig,
    Message,
    Tool,
    MessageRole,
    TextContent,
    AgentEvent,
    AgentEventHandler,
    Usage,
    message_to_dict,
    usage_to_dict,
)
from agent.loop import run_agent_loop
from agent.tools import read_tool, write_tool, edit_tool, bash_tool, WORKSPACE_DIR


def _get_default_system_prompt() -> str:
    """获取默认系统提示词"""
    return f"""你是一个专业的编程助手。通过读取文件、执行命令、编辑代码和创建新文件来帮助用户完成编程任务。

可用工具：
- read: 读取文件内容
- bash: 执行 bash 命令
- edit: 对文件进行精确修改
- write: 创建或覆盖文件

指南：
- 使用 bash 进行文件操作，如 ls、grep、find
- 编辑文件前先使用 read 查看文件内容
- 使用 edit 进行精确修改（old 文本必须完全匹配）
- write 仅用于新文件或完全重写
- 总结操作时，直接输出纯文本 - 不要使用 cat 或 bash 来显示已完成的操作
- 回复要简洁
- 处理文件时清晰显示文件路径

工作目录：{WORKSPACE_DIR}
- 直接使用相对路径，无需包含工作目录"""


def _get_default_model() -> str:
    """从环境变量获取默认模型"""
    return os.environ.get("ANTHROPIC_MODEL", "deepseek-v4-pro")


def _generate_session_id() -> str:
    """生成会话 ID：YYYYMMDD_HHMMSS_xxx 格式"""
    now = time.time()
    ms = int((now - int(now)) * 1000)
    return time.strftime(f"%Y%m%d_%H%M%S_{ms:03d}")


def _current_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)


class Agent:
    """
    Agent 主类

    提供用户友好的接口来与 AI Agent 交互。
    支持事件订阅，可以实时获取 Agent 的执行状态。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_iterations: int = 20,
        tool_execution_mode: str = "parallel",
    ):
        """
        初始化 Agent

        Args:
            system_prompt: 系统提示词（可选）
            model: 使用的模型名称（可选，默认从 ANTHROPIC_MODEL 环境变量读取）
            api_key: API key（可选，默认从 ANTHROPIC_AUTH_TOKEN 环境变量读取）
            base_url: API 基础 URL（可选，默认从 ANTHROPIC_BASE_URL 环境变量读取）
            timeout: 请求超时时间（秒，可选）
            max_iterations: 最大迭代次数
            tool_execution_mode: 工具执行模式，"parallel"（并行，默认）或 "sequential"（串行）
        """
        self._state = AgentState(
            system_prompt=system_prompt or _get_default_system_prompt(),
            model=model or _get_default_model(),
            tools=[read_tool, write_tool, edit_tool, bash_tool],
            messages=[],
            is_streaming=False,
            streaming_message=None,
            pending_tool_calls=[],
            error_message=None,
        )
        self._config = AgentConfig(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_iterations=max_iterations,
            tool_execution_mode=tool_execution_mode,
        )

        # 初始化 session 信息
        self._state.session_id = _generate_session_id()
        self._state.session_created_at = _current_timestamp_ms()
        self._state.usage = Usage()

        # 事件监听器集合
        self._event_listeners: Set[AgentEventHandler] = set()

    @property
    def messages(self) -> List[Message]:
        """获取所有消息历史"""
        return list(self._state.messages)

    @property
    def tools(self) -> List[Tool]:
        """获取所有可用工具"""
        return list(self._state.tools)

    def add_tool(self, tool: Tool) -> None:
        """添加自定义工具"""
        self._state.tools.append(tool)

    def clear_tools(self) -> None:
        """清空所有工具"""
        self._state.tools = []

    def reset(self) -> None:
        """重置对话历史"""
        self._state.messages = []
        self._state.is_streaming = False
        self._state.streaming_message = None
        self._state.pending_tool_calls = []
        self._state.error_message = None
        # 重置 session 信息
        self._state.session_id = _generate_session_id()
        self._state.session_created_at = _current_timestamp_ms()
        self._state.usage = Usage()

    # =========================================================================
    # 事件订阅相关方法
    # =========================================================================

    def subscribe(self, listener: AgentEventHandler) -> Callable[[], None]:
        """
        订阅 Agent 事件

        Args:
            listener: 事件监听器回调函数

        Returns:
            取消订阅的函数
        """
        self._event_listeners.add(listener)

        def unsubscribe():
            self._event_listeners.discard(listener)

        return unsubscribe

    def unsubscribe(self, listener: AgentEventHandler) -> None:
        """
        取消订阅 Agent 事件

        Args:
            listener: 要取消的事件监听器
        """
        self._event_listeners.discard(listener)

    def _emit_event(self, event: AgentEvent) -> None:
        """
        发射事件到所有监听器

        Args:
            event: 要发射的事件
        """
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                import sys
                print(f"[事件监听器错误]: {e}", file=sys.stderr)

    def prompt(self, message: str) -> str:
        """
        发送消息给 Agent 并获取回复

        Args:
            message: 用户消息

        Returns:
            Agent 的文本回复
        """
        new_messages = run_agent_loop(
            self._state,
            self._config,
            message,
            event_sink=self._emit_event,
        )
        self._save_session()
        return self._get_last_assistant_message(new_messages)

    def continue_(self) -> str:
        """
        继续对话（当需要 Agent 执行更多操作时）

        Returns:
            Agent 的文本回复
        """
        if not self._state.messages:
            raise ValueError("没有消息可以继续")

        last_msg = self._state.messages[-1]
        if last_msg.role == MessageRole.ASSISTANT:
            raise ValueError("不能从助手消息继续")

        new_messages = run_agent_loop(
            self._state,
            self._config,
            event_sink=self._emit_event,
        )
        self._save_session()
        return self._get_last_assistant_message(new_messages)

    def _get_last_assistant_message(self, messages: List[Message]) -> str:
        """从消息列表中获取最后一条助手消息的文本内容"""
        for msg in reversed(messages):
            if msg.role == MessageRole.ASSISTANT:
                text_parts = [c.text for c in msg.content if isinstance(c, TextContent)]
                return "\n".join(text_parts)
        return ""

    def _save_session(self) -> None:
        """保存当前会话到文件"""
        import os
        from agent.tools import WORKSPACE_DIR

        # 确保 sessions 目录存在
        sessions_dir = os.path.join(WORKSPACE_DIR, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        # 构建 session 数据
        session_data = {
            "session_id": self._state.session_id,
            "created_at": self._state.session_created_at,
            "model": self._state.model,
            "usage": usage_to_dict(self._state.usage),
            "messages": [message_to_dict(msg) for msg in self._state.messages]
        }

        # 写入文件
        file_path = os.path.join(sessions_dir, f"{self._state.session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    @property
    def is_streaming(self) -> bool:
        """检查 Agent 是否正在流式输出"""
        return self._state.is_streaming

    @property
    def streaming_message(self) -> Optional[Message]:
        """获取当前正在流式输出的消息"""
        return self._state.streaming_message

    @property
    def pending_tool_calls(self) -> List[str]:
        """获取当前待执行的工具调用 ID 列表"""
        return list(self._state.pending_tool_calls)

    @property
    def tool_execution_mode(self) -> str:
        """获取工具执行模式：'parallel'（并行）或 'sequential'（串行）"""
        return self._config.tool_execution_mode

    @tool_execution_mode.setter
    def tool_execution_mode(self, mode: str) -> None:
        """
        设置工具执行模式

        Args:
            mode: 'parallel'（并行）或 'sequential'（串行）
        """
        if mode not in ("parallel", "sequential"):
            raise ValueError("tool_execution_mode 必须是 'parallel' 或 'sequential'")
        self._config.tool_execution_mode = mode
