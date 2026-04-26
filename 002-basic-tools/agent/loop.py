import os
from typing import List, Optional, Callable, Any, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic

from agent.types import (
    Message,
    MessageRole,
    TextContent,
    ThinkingContent,
    ToolCall,
    ToolResult,
    AgentState,
    AgentConfig,
    Tool,
    AgentEvent,
    AgentEventHandler,
    AgentEventType,
    create_agent_start_event,
    create_agent_end_event,
    create_turn_start_event,
    create_turn_end_event,
    create_message_start_event,
    create_message_update_event,
    create_message_end_event,
    create_tool_execution_start_event,
    create_tool_execution_update_event,
    create_tool_execution_end_event,
)


def _tool_to_dict(tool: Tool) -> dict:
    """将工具对象转换为 Anthropic API 需要的字典格式"""
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": {
            "type": tool.parameters.type,
            "properties": tool.parameters.properties,
            "required": tool.parameters.required,
        },
    }


def _message_to_anthropic(message: Message) -> dict:
    """将消息转换为 Anthropic API 格式"""
    content = []
    for block in message.content:
        if isinstance(block, ThinkingContent):
            content.append({"type": "thinking", "thinking": block.thinking})
        elif isinstance(block, TextContent):
            content.append({"type": "text", "text": block.text})
        elif isinstance(block, ToolCall):
            content.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.arguments,
            })
        elif isinstance(block, ToolResult):
            text_content = "\n".join(c.text for c in block.content)
            content.append({
                "type": "tool_result",
                "tool_use_id": block.tool_call_id,
                "content": text_content,
                "is_error": block.is_error,
            })

    return {
        "role": message.role.value if message.role != MessageRole.TOOL_RESULT else "user",
        "content": content if content else [{"type": "text", "text": ""}],
    }


def _parse_assistant_content(anthropic_message: Any) -> List[TextContent | ToolCall]:
    """解析助手返回的内容"""
    content = []
    for block in anthropic_message.content:
        if block.type == "thinking":
            content.append(ThinkingContent(thinking=block.thinking))
        elif block.type == "text":
            content.append(TextContent(text=block.text))
        elif block.type == "tool_use":
            content.append(ToolCall(
                id=block.id,
                name=block.name,
                arguments=block.input,
            ))
    return content


def _emit_event(event_sink: Optional[AgentEventHandler], event: AgentEvent) -> None:
    """发射事件"""
    if event_sink:
        try:
            event_sink(event)
        except Exception as e:
            import sys
            print(f"[事件处理错误]: {e}", file=sys.stderr)


def _execute_single_tool(
    tool_call: ToolCall,
    tools: List[Tool],
    state: AgentState,
    event_sink: Optional[AgentEventHandler],
) -> Tuple[ToolCall, ToolResult, Message]:
    """执行单个工具（用于并行执行）"""
    # 发射 tool_execution_start 事件
    _emit_event(event_sink, create_tool_execution_start_event(
        tool_call_id=tool_call.id,
        tool_name=tool_call.name,
        args=tool_call.arguments,
    ))

    tool = next((t for t in tools if t.name == tool_call.name), None)
    if not tool:
        tool_result = ToolResult(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            content=[TextContent(text=f"未知工具: {tool_call.name}")],
            is_error=True,
        )
    else:
        # 定义工具更新回调
        def create_tool_update_callback(tc_id=tool_call.id, tc_name=tool_call.name, tc_args=tool_call.arguments):
            def callback(partial_result: Any):
                _emit_event(event_sink, create_tool_execution_update_event(
                    tool_call_id=tc_id,
                    tool_name=tc_name,
                    args=tc_args,
                    partial_result=partial_result,
                ))
            return callback

        tool_result = tool.execute(
            tool_call.id,
            tool_call.arguments,
            create_tool_update_callback(),
        )

    result_msg = Message(
        role=MessageRole.TOOL_RESULT,
        content=[tool_result],
    )

    # 发射 tool_execution_end 事件
    _emit_event(event_sink, create_tool_execution_end_event(
        tool_call_id=tool_call.id,
        tool_name=tool_call.name,
        result=tool_result,
        is_error=tool_result.is_error,
    ))

    return tool_call, tool_result, result_msg


def run_agent_loop(
    state: AgentState,
    config: AgentConfig,
    user_message: Optional[str] = None,
    event_sink: Optional[AgentEventHandler] = None,
) -> List[Message]:
    """
    运行 Agent 主循环

    Args:
        state: Agent 状态
        config: Agent 配置
        user_message: 用户消息（可选）
        event_sink: 事件接收器回调函数（可选）
        tool_execution_mode: 工具执行模式，"parallel"（并行）或 "sequential"（串行）

    Returns:
        本次循环新增的消息列表
    """
    # 从环境变量获取配置，如果 config 中没有提供的话
    api_key = config.api_key or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("必须提供 API key 或设置 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY 环境变量")

    base_url = config.base_url or os.environ.get("ANTHROPIC_BASE_URL")

    timeout = config.timeout
    if timeout is None:
        timeout_ms = os.environ.get("API_TIMEOUT_MS")
        if timeout_ms:
            timeout = float(timeout_ms) / 1000.0

    # 构建客户端参数
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    if timeout:
        client_kwargs["timeout"] = timeout

    client = Anthropic(**client_kwargs)

    new_messages: List[Message] = []

    # 标记开始流式输出
    state.is_streaming = True

    # 发射 agent_start 事件
    _emit_event(event_sink, create_agent_start_event())

    if user_message:
        user_msg = Message(
            role=MessageRole.USER,
            content=[TextContent(text=user_message)],
        )
        state.messages.append(user_msg)
        new_messages.append(user_msg)

        # 发射 message_start 和 message_end 事件
        _emit_event(event_sink, create_message_start_event(user_msg))
        _emit_event(event_sink, create_message_end_event(user_msg))

    iteration = 0
    # 无限制时永远继续，直到模型不再调用工具为止
    while True:
        if config.max_iterations is not None and iteration >= config.max_iterations:
            break
        iteration += 1

        # 发射 turn_start 事件
        _emit_event(event_sink, create_turn_start_event())

        anthropic_messages = [_message_to_anthropic(m) for m in state.messages]
        tools = [_tool_to_dict(t) for t in state.tools]

        # 使用流式 API 响应
        assistant_content: List[TextContent | ThinkingContent | ToolCall] = []
        current_text = ""
        current_thinking = ""
        current_tool_calls: List[ToolCall] = []
        tool_call_inputs: Dict[str, str] = {}  # 用于累积工具调用输入

        # 创建初始的 assistant message 用于流式更新
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content=[],
        )
        state.streaming_message = assistant_msg

        # 发射 message_start 事件
        _emit_event(event_sink, create_message_start_event(assistant_msg))

        # 流式调用 API
        with client.messages.stream(
            model=state.model,
            max_tokens=4096,
            system=state.system_prompt,
            messages=anthropic_messages,
            tools=tools if tools else None,
        ) as stream:
            for event in stream:
                if event.type == "message_start":
                    pass
                elif event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "thinking":
                        current_thinking = block.thinking or ""
                    elif block.type == "text":
                        current_text = block.text or ""
                    elif block.type == "tool_use":
                        # 初始化工具调用
                        tool_call = ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input or {},
                        )
                        current_tool_calls.append(tool_call)
                        tool_call_inputs[block.id] = ""
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        current_thinking += delta.thinking
                        # 更新消息内容（不对外发射 UI 事件）
                        assistant_content = []
                        if current_thinking:
                            assistant_content.append(ThinkingContent(thinking=current_thinking))
                        if current_text:
                            assistant_content.append(TextContent(text=current_text))
                        assistant_content.extend(current_tool_calls)
                        assistant_msg.content = assistant_content
                        state.streaming_message = assistant_msg
                    elif delta.type == "text_delta":
                        current_text += delta.text
                        # 更新 message 并发射 message_update 事件
                        assistant_content = []
                        if current_thinking:
                            assistant_content.append(ThinkingContent(thinking=current_thinking))
                        if current_text:
                            assistant_content.append(TextContent(text=current_text))
                        assistant_content.extend(current_tool_calls)
                        assistant_msg.content = assistant_content
                        state.streaming_message = assistant_msg
                        _emit_event(event_sink, create_message_update_event(
                            message=assistant_msg,
                            delta=delta.text,
                        ))
                    elif delta.type == "input_json_delta":
                        # 更新工具调用参数
                        block_index = getattr(event, 'index', len(current_tool_calls) - 1)
                        if 0 <= block_index < len(current_tool_calls):
                            tool_call = current_tool_calls[block_index]
                            # 累积 JSON 输入 (简化处理)
                            tool_call_inputs[tool_call.id] = tool_call_inputs.get(tool_call.id, "") + delta.partial_json

                        # 更新消息内容并发射事件
                        assistant_content = []
                        if current_thinking:
                            assistant_content.append(ThinkingContent(thinking=current_thinking))
                        if current_text:
                            assistant_content.append(TextContent(text=current_text))
                        assistant_content.extend(current_tool_calls)
                        assistant_msg.content = assistant_content
                        state.streaming_message = assistant_msg
                        _emit_event(event_sink, create_message_update_event(
                            message=assistant_msg,
                            delta_tool_call=tool_call if 0 <= block_index < len(current_tool_calls) else None,
                        ))
                elif event.type == "content_block_stop":
                    pass
                elif event.type == "message_delta":
                    pass
                elif event.type == "message_stop":
                    pass

        # 获取完整的响应
        response = stream.get_final_message()

        # 累加 token 使用量
        if hasattr(response, 'usage'):
            state.usage.input_tokens += getattr(response.usage, 'input_tokens', 0)
            state.usage.output_tokens += getattr(response.usage, 'output_tokens', 0)

        # 记录本轮 API 原始返回
        state.api_calls.append(response.model_dump())

        # 解析完整的响应
        assistant_content = _parse_assistant_content(response)
        assistant_msg.content = assistant_content
        state.messages.append(assistant_msg)
        new_messages.append(assistant_msg)
        state.streaming_message = None

        # 发射 message_end 事件
        _emit_event(event_sink, create_message_end_event(assistant_msg))

        tool_calls = [c for c in assistant_content if isinstance(c, ToolCall)]
        tool_results: List[Message] = []

        if not tool_calls:
            # 没有工具调用，发射 turn_end 事件并结束
            _emit_event(event_sink, create_turn_end_event(assistant_msg, tool_results))
            break

        # 执行工具调用
        if config.tool_execution_mode == "parallel" and len(tool_calls) > 1:
            # 并行执行工具调用
            tool_results_map: Dict[str, Tuple[ToolResult, Message]] = {}

            with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(
                        _execute_single_tool,
                        tool_call,
                        state.tools,
                        state,
                        event_sink,
                    ): tool_call
                    for tool_call in tool_calls
                }

                # 按原始顺序收集结果
                for future in as_completed(futures):
                    tool_call, tool_result, result_msg = future.result()
                    tool_results_map[tool_call.id] = (tool_result, result_msg)

            # 多个工具结果合并到一条消息（API 要求 assistant 的所有
            # tool_use 必须在紧接着的下一条消息里全部给出 tool_result）
            combined_result_msg = Message(
                role=MessageRole.TOOL_RESULT,
                content=[],
            )
            for tool_call in tool_calls:
                tool_result, _ = tool_results_map[tool_call.id]
                combined_result_msg.content.append(tool_result)
                if tool_call.id in state.pending_tool_calls:
                    state.pending_tool_calls.remove(tool_call.id)
            state.messages.append(combined_result_msg)
            new_messages.append(combined_result_msg)
            tool_results.append(combined_result_msg)
        else:
            # 串行执行工具调用
            for tool_call in tool_calls:
                state.pending_tool_calls.append(tool_call.id)
                _, tool_result, result_msg = _execute_single_tool(
                    tool_call,
                    state.tools,
                    state,
                    event_sink,
                )
                state.messages.append(result_msg)
                new_messages.append(result_msg)
                tool_results.append(result_msg)
                if tool_call.id in state.pending_tool_calls:
                    state.pending_tool_calls.remove(tool_call.id)

        # 发射 turn_end 事件
        _emit_event(event_sink, create_turn_end_event(assistant_msg, tool_results))

    # 发射 agent_end 事件
    state.is_streaming = False
    _emit_event(event_sink, create_agent_end_event(new_messages))

    return new_messages
