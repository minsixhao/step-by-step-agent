"""
终端渲染器

主渲染器类，订阅 Agent 事件系统，协调所有 UI 组件。
"""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

from agent.types import (
    AgentEvent,
    AgentEventType,
    Message,
    MessageRole,
    TextContent,
    ToolCall,
    ToolResult,
)
from agent.ui.colors import Colors
from agent.ui.markdown import MarkdownRenderer
from agent.ui.spinner import Spinner


@dataclass
class ActiveToolInfo:
    """追踪进行中的工具信息"""
    tool_call_id: str
    tool_name: str
    args: Dict[str, Any]
    start_time: float
    spinner: Spinner


class TerminalRenderer:
    """
    终端渲染器

    订阅 Agent 事件系统，提供美观的终端可视化输出。
    """

    def __init__(self):
        # 状态管理
        self.active_tools: Dict[str, ActiveToolInfo] = {}
        self.current_message: Optional[Message] = None
        self.agent_start_time: Optional[float] = None
        self.current_turn_start: Optional[float] = None

        # 子组件
        self.markdown_renderer = MarkdownRenderer()

        # 输出状态
        self._in_streaming_output = False
        self._header_printed = False

    def __call__(self, event: AgentEvent) -> None:
        """
        事件入口点

        Args:
            event: Agent 事件
        """
        handler_name = f"_on_{event.type.value}"
        handler = getattr(self, handler_name, self._on_unknown_event)
        handler(event)

    # ==========================================
    # 事件处理方法
    # ==========================================

    def _on_agent_start(self, event: AgentEvent) -> None:
        """处理 agent_start 事件"""
        self.agent_start_time = time.time()
        print()  # 空行分隔

    def _on_agent_end(self, event: AgentEvent) -> None:
        """处理 agent_end 事件"""
        # 确保所有工具都已停止
        for tool_info in list(self.active_tools.values()):
            tool_info.spinner.stop(success=None)
        self.active_tools.clear()

        # 显示总耗时
        if self.agent_start_time:
            elapsed = time.time() - self.agent_start_time
            print()
            print(f"{Colors.DIM}完成，总耗时: {elapsed:.2f}s{Colors.RESET}")

    def _on_turn_start(self, event: AgentEvent) -> None:
        """处理 turn_start 事件"""
        self.current_turn_start = time.time()

    def _on_turn_end(self, event: AgentEvent) -> None:
        """处理 turn_end 事件"""
        pass

    def _on_message_start(self, event: AgentEvent) -> None:
        """处理 message_start 事件"""
        if event.message:
            self.current_message = event.message
            self._header_printed = False
            self._in_streaming_output = False

            # 如果是用户消息，立即显示（用户消息不是流式的）
            if event.message.role == MessageRole.USER:
                self._render_message_header(event.message)
                self._header_printed = True
                self._render_message_content(event.message, is_complete=True)

    def _on_message_update(self, event: AgentEvent) -> None:
        """处理 message_update 事件（流式输出）"""
        if event.delta:
            # 第一次输出时打印头
            if not self._header_printed and self.current_message:
                self._render_message_header(self.current_message)
                self._header_printed = True
                print("  ", end="", flush=True)  # 初始缩进

            print(event.delta, end="", flush=True)
            self._in_streaming_output = True
        elif event.delta_tool_call:
            # 工具调用更新，暂不处理
            pass

    def _on_message_end(self, event: AgentEvent) -> None:
        """处理 message_end 事件"""
        if event.message:
            # 如果是用户消息，已经在 message_start 处理过了
            if event.message.role == MessageRole.USER:
                self.current_message = None
                return

            # 如果没有流式输出（没有内容或只有工具调用），显示头
            if not self._header_printed:
                self._render_message_header(event.message)
                self._header_printed = True

            # 如果有流式输出，补换行
            if self._in_streaming_output:
                print()

            # 只渲染非文本内容（工具调用等），文本已经通过流式输出了
            self._render_non_text_content(event.message)

        self.current_message = None
        self._in_streaming_output = False
        self._header_printed = False

    def _on_tool_execution_start(self, event: AgentEvent) -> None:
        """处理 tool_execution_start 事件"""
        if not event.tool_call_id or not event.tool_name:
            return

        # 确保新起一行
        if self._in_streaming_output:
            print()
            self._in_streaming_output = False

        # 创建并启动 spinner
        args_str = self._format_args(event.args or {})
        message = f"{Colors.BOLD}{event.tool_name}{Colors.RESET}({args_str})"
        spinner = Spinner(message, color=Colors.YELLOW)
        spinner.start()

        # 记录工具信息
        tool_info = ActiveToolInfo(
            tool_call_id=event.tool_call_id,
            tool_name=event.tool_name,
            args=event.args or {},
            start_time=time.time(),
            spinner=spinner,
        )
        self.active_tools[event.tool_call_id] = tool_info

    def _on_tool_execution_update(self, event: AgentEvent) -> None:
        """处理 tool_execution_update 事件"""
        # 可以在这里显示部分结果
        pass

    def _on_tool_execution_end(self, event: AgentEvent) -> None:
        """处理 tool_execution_end 事件"""
        if not event.tool_call_id:
            return

        tool_info = self.active_tools.pop(event.tool_call_id, None)
        if tool_info:
            # 停止 spinner
            success = not event.is_error if event.is_error is not None else True
            tool_info.spinner.stop(success=success)

            # 显示工具结果
            if event.result:
                self._render_tool_result(event.result)

    def _on_unknown_event(self, event: AgentEvent) -> None:
        """处理未知事件"""
        pass

    # ==========================================
    # 渲染辅助方法
    # ==========================================

    def _render_message_header(self, message: Message) -> None:
        """
        渲染消息头

        [点] [类型标签] [时间]
        """
        dot = self._get_dot_for_role(message.role)
        label = self._get_label_for_role(message.role)
        time_str = self._format_timestamp(message.timestamp)

        print(f"{dot} {label} {time_str}")

    def _render_message_content(self, message: Message, is_complete: bool = False) -> None:
        """
        渲染消息内容（用于非流式消息，如用户消息）

        Args:
            message: 消息对象
            is_complete: 是否是完整消息
        """
        for block in message.content:
            if isinstance(block, TextContent) and block.text:
                rendered = self.markdown_renderer.render(block.text)
                for line in rendered.split("\n"):
                    print(f"  {line}")

    def _render_non_text_content(self, message: Message) -> None:
        """
        渲染非文本内容（工具调用等）
        文本内容已经通过流式输出显示了
        """
        for block in message.content:
            if isinstance(block, ToolCall):
                # 工具调用会在 tool_execution_start 事件中处理
                pass
            elif isinstance(block, ToolResult):
                # 工具结果会在 tool_execution_end 事件中处理
                pass

    def _render_tool_result(self, result: ToolResult) -> None:
        """渲染工具结果"""
        # 收集结果文本
        text_parts = [c.text for c in result.content if c.text.strip()]
        if not text_parts:
            return

        text = "\n".join(text_parts)

        # 限制输出长度，避免太长
        lines = text.split("\n")
        if len(lines) > 20:
            lines = lines[:20]
            lines.append(f"... (已截断，共 {len(text.splitlines())} 行)")
            text = "\n".join(lines)

        # 缩进显示
        for line in text.split("\n"):
            print(f"  {Colors.DIM}└─{Colors.RESET} {line}")

    def _get_dot_for_role(self, role: MessageRole) -> str:
        """根据消息角色获取对应的点"""
        if role == MessageRole.USER:
            return f"{Colors.CYAN}●{Colors.RESET}"
        elif role == MessageRole.ASSISTANT:
            return f"{Colors.WHITE}○{Colors.RESET}"
        elif role == MessageRole.TOOL_RESULT:
            return f"{Colors.GREEN}●{Colors.RESET}"
        else:
            return f"{Colors.DIM}○{Colors.RESET}"

    def _get_label_for_role(self, role: MessageRole) -> str:
        """根据消息角色获取标签"""
        if role == MessageRole.USER:
            return f"{Colors.BOLD}{Colors.CYAN}USER{Colors.RESET}"
        elif role == MessageRole.ASSISTANT:
            return f"{Colors.BOLD}{Colors.WHITE}ASSISTANT{Colors.RESET}"
        elif role == MessageRole.TOOL_RESULT:
            return f"{Colors.BOLD}{Colors.YELLOW}TOOL{Colors.RESET}"
        else:
            return f"{Colors.BOLD}UNKNOWN{Colors.RESET}"

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """格式化时间戳"""
        timestamp_s = timestamp_ms / 1000.0
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp_s))
        return f"{Colors.DIM}[{time_str}]{Colors.RESET}"

    def _format_args(self, args: Dict[str, Any]) -> str:
        """格式化工具参数为简洁字符串"""
        parts = []
        for key, value in args.items():
            if isinstance(value, str):
                # 截断长字符串
                if len(value) > 50:
                    value = value[:47] + "..."
                # 显示为简洁的字符串
                parts.append(f"{key}={repr(value)}")
            else:
                parts.append(f"{key}={value}")
        return ", ".join(parts)
