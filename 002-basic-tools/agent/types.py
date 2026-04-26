"""
数据类型定义

定义 Agent 所需的核心数据类型。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "toolResult"


@dataclass
class TextContent:
    """文本内容块"""
    type: str = "text"
    text: str = ""


@dataclass
class ThinkingContent:
    """思考内容块（DeepSeek 等模型的 thinking 输出）"""
    type: str = "thinking"
    thinking: str = ""


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    tool_name: str
    content: List[TextContent]
    is_error: bool = False
    details: Any = None


@dataclass
class Usage:
    """Token 使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


MessageContent = Union[TextContent, ThinkingContent, ToolCall, ToolResult]


@dataclass
class Message:
    """消息"""
    role: MessageRole
    content: List[MessageContent]
    timestamp: int = field(default_factory=lambda: __import__("time").time_ns() // 1_000_000)


@dataclass
class ToolParameters:
    """工具参数定义"""
    type: str = "object"
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: ToolParameters
    execute: Callable[[str, Dict[str, Any], Optional[Callable[[Any], None]]], ToolResult]


@dataclass
class AgentState:
    """Agent 状态"""
    system_prompt: str = ""
    messages: List[Message] = field(default_factory=list)
    tools: List[Tool] = field(default_factory=list)
    model: str = "deepseek-v4-pro"
    is_streaming: bool = False
    streaming_message: Optional[Message] = None
    pending_tool_calls: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    # 新增字段
    session_id: str = ""
    session_created_at: int = 0
    usage: Usage = field(default_factory=Usage)
    api_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Agent 配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[float] = None
    max_iterations: Optional[int] = None
    tool_execution_mode: str = "parallel"  # "parallel" 或 "sequential"


# =============================================================================
# Agent 事件类型定义
# =============================================================================

class AgentEventType(Enum):
    """Agent 事件类型"""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    MESSAGE_START = "message_start"
    MESSAGE_UPDATE = "message_update"
    MESSAGE_END = "message_end"
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_EXECUTION_UPDATE = "tool_execution_update"
    TOOL_EXECUTION_END = "tool_execution_end"


@dataclass
class AgentEvent:
    """Agent 事件"""
    type: AgentEventType
    messages: Optional[List[Message]] = None
    message: Optional[Message] = None
    tool_results: Optional[List[Message]] = None
    delta: Optional[str] = None
    delta_tool_call: Optional[ToolCall] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    partial_result: Optional[Any] = None
    result: Optional[ToolResult] = None
    is_error: Optional[bool] = None


# 事件回调类型
AgentEventHandler = Callable[[AgentEvent], Union[None, Any]]


# 便捷函数创建各种事件
def create_agent_start_event() -> AgentEvent:
    return AgentEvent(type=AgentEventType.AGENT_START)


def create_agent_end_event(messages: List[Message]) -> AgentEvent:
    return AgentEvent(type=AgentEventType.AGENT_END, messages=messages)


def create_turn_start_event() -> AgentEvent:
    return AgentEvent(type=AgentEventType.TURN_START)


def create_turn_end_event(message: Message, tool_results: List[Message]) -> AgentEvent:
    return AgentEvent(type=AgentEventType.TURN_END, message=message, tool_results=tool_results)


def create_message_start_event(message: Message) -> AgentEvent:
    return AgentEvent(type=AgentEventType.MESSAGE_START, message=message)


def create_message_update_event(
    message: Message,
    delta: Optional[str] = None,
    delta_tool_call: Optional[ToolCall] = None,
) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.MESSAGE_UPDATE,
        message=message,
        delta=delta,
        delta_tool_call=delta_tool_call,
    )


def create_message_end_event(message: Message) -> AgentEvent:
    return AgentEvent(type=AgentEventType.MESSAGE_END, message=message)


def create_tool_execution_start_event(
    tool_call_id: str,
    tool_name: str,
    args: Dict[str, Any],
) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOOL_EXECUTION_START,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        args=args,
    )


def create_tool_execution_update_event(
    tool_call_id: str,
    tool_name: str,
    args: Dict[str, Any],
    partial_result: Any,
) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOOL_EXECUTION_UPDATE,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        args=args,
        partial_result=partial_result,
    )


def create_tool_execution_end_event(
    tool_call_id: str,
    tool_name: str,
    result: ToolResult,
    is_error: bool,
) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOOL_EXECUTION_END,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        result=result,
        is_error=is_error,
    )


# =============================================================================
# 序列化辅助函数
# =============================================================================

def message_to_dict(message: Message) -> dict:
    """将 Message 转换为 JSON 可序列化的 dict"""
    content_dicts = []
    for block in message.content:
        if isinstance(block, ThinkingContent):
            content_dicts.append({
                "type": "thinking",
                "thinking": block.thinking
            })
        elif isinstance(block, TextContent):
            content_dicts.append({
                "type": "text",
                "text": block.text
            })
        elif isinstance(block, ToolCall):
            content_dicts.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.arguments
            })
        elif isinstance(block, ToolResult):
            content_dicts.append({
                "type": "tool_result",
                "tool_use_id": block.tool_call_id,
                "tool_name": block.tool_name,
                "content": [c.text for c in block.content],
                "is_error": block.is_error
            })
    return {
        "role": message.role.value,
        "content": content_dicts,
        "timestamp": message.timestamp
    }


def usage_to_dict(usage: Usage) -> dict:
    """将 Usage 转换为 JSON 可序列化的 dict"""
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens
    }
