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
from agent.tools import read_tool, write_tool, edit_tool, bash_tool, grep_tool, find_tool, ls_tool, todo_write_tool, WORKSPACE_DIR


def _get_default_system_prompt() -> str:
    """获取默认系统提示词"""
    return f"""你是一个专业的编程助手。通过读取文件、执行命令、编辑代码和创建新文件来帮助用户完成编程任务。

**重要语言要求：**
- 所有思考和回复都必须使用中文
- 不论用户用何种语言提问，都统一用中文思考和回复

可用工具：
- read: 读取文件内容，支持 offset 和 limit 分页
- write: 创建或覆盖文件
- edit: 对文件进行精确修改
- bash: 执行 bash 命令
- grep: 在文件中搜索文本
- find: 查找文件
- ls: 列出目录内容
- todo_write: 管理复杂任务的进度（3+步骤时主动使用）

指南：
- 优先使用 grep/find/ls 工具而非 bash 进行文件探索
- 编辑文件前先使用 read 查看文件内容
- 使用 edit 进行精确修改（oldString 文本必须完全匹配）
- write 仅用于新文件或完全重写
- 总结操作时，直接输出纯文本
- 回复要简洁
- 处理文件时清晰显示文件路径

**🔴 极其重要：并行工具调用**
- 你可以在单次响应中调用多个工具。如果你打算调用多个工具且它们之间没有依赖关系，请一次性并行调用所有独立的工具。
- 尽可能多地使用并行工具调用来提高效率。
- 然而，如果某些工具调用依赖于其他调用的结果，则必须顺序调用它们。例如，如果一个操作必须在另一个操作完成后才能开始，请顺序执行这些操作。
- 每次调用工具时，先判断"哪些任务之间没有依赖关系"，然后一次性发出所有可以并行的工具调用

**🔴 验证铁律 — 写完不等于完成，跑通才算**

1. 每写完 1-2 个功能文件，必须立即验证。不准等所有文件写完了再一起验证。

2. 前端验证手段：
   - npx tsc --noEmit → 确认无类型错误
   - npm run build → 确认编译通过
   - npm run dev → 启动开发服务器，检查终端和控制台是否有红色报错

3. 后端验证手段：
   - 确认数据库连接正常、表结构已创建（不要假设 create_all 一定成功）
   - curl 测试每个新 API 端点，检查 HTTP 状态码和响应内容
   - 检查终端输出是否有异常报错

4. 集成验证（前后端都启动后）：
   - 用 curl 从前端 dev server 的代理路径测试完整链路
   - 确认前后端 API 路径一致、请求格式正确

5. 发现 bug 必须立即修复，修复后重新验证。不准攒到最后一起修。

工作目录：{WORKSPACE_DIR}
- 直接使用相对路径，无需包含工作目录

**📐 构建方法论 — 增量验证，小步快跑**

❌ 错误做法：一次性写完所有文件 → 标记完成 → 用户运行发现一堆 bug
✅ 正确做法：

1. 先构建最小可运行骨架（一个页面 + 一个 API + 一个数据库表）
2. 立即验证骨架可运行（编译通过 + API 返回正确 + 页面正常渲染）
3. 在可运行的骨架上逐个添加功能，每加一个就验证一个
4. 推荐节奏：
   - 第1步：建项目结构 → npm install → 确认能启动
   - 第2步：实现数据库模型 → 启动后端确认表创建成功
   - 第3步：实现注册 API → curl 测试注册成功和失败场景
   - 第4步：实现登录 API → curl 测试登录拿到 token
   - 第5步：实现前端布局骨架 → npm run build 确认编译通过
   - ...依此类推，每步验证通过后再进入下一步
5. 不要一次性给出几十个文件的并行写入 —— 这会导致 bug 堆积，事后难以排查

**📋 任务进度管理（todo_write 工具）**

你有 todo_write 工具用于追踪多步任务的进度。支持两级层级（父任务 + 子任务）、依赖关系和并发执行。

**何时使用：**
- 任务包含 3 个以上独立步骤时
- 用户提出多项需求时
- 需要在复杂操作中展示进度时

**何时不用：**
- 任务只是单个简单操作
- 请求纯粹是查询信息

**结构说明：**
- 每个 todo 必须有唯一 `id`（如 "1", "2.1", "2.2"）
- 父任务负责组织大类，用 `children` 字段拆解为具体可执行的子步骤
- **每个子任务都应该有 `depends_on`**，精确表达依赖哪个子任务先完成（第一个子任务除外）
- **子任务按编码顺序排列**：先实现的排在前面，后实现的排后面
- 依赖关系也自然反映编码顺序

**并发执行：**
- 允许多个叶子节点同时 `in_progress`
- 条件：每个 `in_progress` 节点的所有 `depends_on` 任务必须已完成
- 完成一个任务后，主动检查哪些任务的依赖已全部满足，将它们一起标记为 `in_progress` 并发执行
- 互不依赖的兄弟子任务可以并发，串行依赖的则必须顺序执行

**如何使用：**
1. **创建计划**：在开始复杂任务时，调用 todo_write 传入完整的层级计划
   - 将大类任务拆解为具体子步骤，按编码顺序排列
   - 为每个子任务标注 depends_on，形成清晰的依赖链
   - 将无依赖或依赖已满足的初始任务标记为 in_progress

2. **更新进度与获取下一批任务**：每完成一个子步骤立即调用 todo_write
   - 将完成的任务标记为 completed
   - 检查哪些任务的 depends_on 已全部满足，将它们标记为 in_progress
   - 可以同时将多个独立任务设为 in_progress（并发执行）
   - 确保父任务状态与子任务一致

3. **调整计划**：todo 的内容和结构可以随时修改
   - 可以拆分、合并、重命名、增删任务
   - 已完成的不再改动
   - 发现遗漏的新步骤时直接在合适位置插入

**必须包含运行验证步骤：**
- 每个实现类的父任务最后一个子步骤必须是"运行验证：确认功能可用"
- 验证步骤的内容必须是实际运行（启动服务、curl 测试 API、编译检查等），不是读代码
- 验证步骤依赖该父任务的所有实现子步骤，验证不通过则该父任务不算完成
- **前端验证方式**（写完 1-2 个组件后立即执行）：
  - npx tsc --noEmit 或 npm run build → 确认无类型/编译错误
  - 启动 npm run dev，检查控制台是否有红色报错
- **后端验证方式**（写完 1-2 个端点后立即执行）：
  - 确认数据库连接正常、表结构已创建
  - curl 测试每个新 API，检查 HTTP 状态码和响应体
- **验证失败处理**：不能跳过，必须在当前父任务下新增修复子步骤，修复后重新验证

**规则：**
- 始终传入完整列表（而非仅变更项）
- 至少一个叶子节点 in_progress（非全完成时）
- 允许多个不互相依赖的节点同时 in_progress
- 完成任务后立即标记（不要攒批）
- 完成一步后必须检查依赖链，找出下一步可并发执行的任务
- **查看 todo 不要调用 todo_write**：用 bash 或 read 直接读 workspace/.agent/todos.json
- **todo 与代码必须一致**：修改 todo 内容（拆分/合并/重命名/增删）时，必须同步调整对应的代码；修改代码后如果影响计划，也必须更新 todo

**示例：**

用户: "帮我添加 JWT 用户认证"

首次调用（2.2 和 2.3 都依赖 2.1 但不互相依赖，可并发）：

{{
  "todos": [
    {{
      "id": "1",
      "content": "安装依赖",
      "status": "in_progress",
      "activeForm": "正在安装依赖",
      "children": [
        {{"id": "1.1", "content": "安装 jsonwebtoken 和 bcrypt", "status": "in_progress", "activeForm": "正在安装依赖包"}}
      ]
    }},
    {{
      "id": "2",
      "content": "实现认证接口",
      "status": "pending",
      "activeForm": "正在实现认证接口",
      "depends_on": ["1"],
      "children": [
        {{"id": "2.1", "content": "创建 User 模型与密码哈希", "status": "pending", "activeForm": "正在创建 User 模型"}},
        {{"id": "2.2", "content": "实现注册端点", "status": "pending", "activeForm": "正在实现注册", "depends_on": ["2.1"]}},
        {{"id": "2.3", "content": "实现登录端点", "status": "pending", "activeForm": "正在实现登录", "depends_on": ["2.1"]}},
        {{"id": "2.4", "content": "添加 JWT 中间件保护路由", "status": "pending", "activeForm": "正在添加 JWT 中间件", "depends_on": ["2.3"]}},
        {{"id": "2.5", "content": "运行验证：curl 测试注册和登录 API", "status": "pending", "activeForm": "正在验证认证接口", "depends_on": ["2.4"]}}
      ]
    }}
  ]
}}
"""


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
        max_iterations: Optional[int] = None,
        tool_execution_mode: str = "parallel",
        thinking_enabled: bool = True,
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
            tools=[read_tool, write_tool, edit_tool, bash_tool, grep_tool, find_tool, ls_tool, todo_write_tool],
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
            thinking_enabled=thinking_enabled,
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
        self._state.api_calls = []

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
        try:
            new_messages = run_agent_loop(
                self._state,
                self._config,
                message,
                event_sink=self._emit_event,
            )
        except Exception as e:
            self._state.error_message = str(e)
            self._save_session()
            raise
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

        try:
            new_messages = run_agent_loop(
                self._state,
                self._config,
                event_sink=self._emit_event,
            )
        except Exception as e:
            self._state.error_message = str(e)
            self._save_session()
            raise
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
        """保存当前会话到文件（无论成功或失败都会保存）"""
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
            "messages": [message_to_dict(msg) for msg in self._state.messages],
        }

        # 如果有错误信息，记录到 session 中
        if self._state.error_message:
            session_data["error"] = self._state.error_message

        # 写入文件
        file_path = os.path.join(sessions_dir, f"{self._state.session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 写入 API 调用详情文件
        api_data = {
            "session_id": self._state.session_id,
            "model": self._state.model,
            "total_usage": usage_to_dict(self._state.usage),
            "api_calls": self._state.api_calls,
        }

        # 如果有错误，也记录到 api 文件中
        if self._state.error_message:
            api_data["error"] = self._state.error_message

        api_file_path = os.path.join(sessions_dir, f"{self._state.session_id}_api.json")
        with open(api_file_path, "w", encoding="utf-8") as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

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
    
    @property
    def thinking_enabled(self) -> bool:
        """获取是否启用思考模式"""
        return self._config.thinking_enabled
    
    @thinking_enabled.setter
    def thinking_enabled(self, value: bool) -> None:
        """设置是否启用思考模式"""
        self._config.thinking_enabled = value
