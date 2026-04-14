# v001: Minimal Agent 设计文档

## 阶段目标

**问题**：如何从零构建一个可用的 Agent？

**目标**：创建一个"最简可用"的 Agent 原型，验证核心概念：
- Agent 能够调用 LLM
- LLM 能够使用工具（文件操作 + 命令执行）
- 有基本的用户交互界面

## 设计思路

### 1. 核心架构分层

```
┌─────────────────────────────────────┐
│   Agent (用户友好接口)               │
├─────────────────────────────────────┤
│   Loop (主循环: Think → Act → Observe) │
├─────────────────────────────────────┤
│   Types (数据模型定义)               │
├─────────────────────────────────────┤
│   Tools (工具实现)                   │
└─────────────────────────────────────┘
```

**为什么这样设计？**
- **关注点分离**：数据、逻辑、接口各司其职
- **可测试性**：每层可以独立测试
- **可演进性**：后续可以替换某一层而不影响其他层

### 2. 数据模型设计

使用 Python dataclass 定义核心类型：

```python
# 消息相关
Message → role + content[TextContent|ToolCall|ToolResult]

# 工具相关
Tool → name + description + parameters + execute()

# 状态分离
AgentState (可变状态) vs AgentConfig (不可变配置)
```

**为什么这样设计？**
- **dataclass**：简洁，自动生成 `__init__`、`__repr__` 等方法
- **State vs Config 分离**：明确区分"运行时状态"和"启动配置"
- **Union 类型**：MessageContent 可以是多种类型，灵活匹配 LLM API

### 3. 主循环设计

```
while iteration < max_iterations:
    1. 调用 LLM 获取响应（流式）
    2. 解析响应，提取 ToolCall
    3. 执行工具（支持并行/串行）
    4. 将 ToolResult 放回消息历史
    5. 如果没有 ToolCall，结束
```

**为什么这样设计？**
- **流式输出**：用户体验更好，不用等完整响应
- **并行工具执行**：多个独立工具调用可以同时执行，提升效率
- **可配置 max_iterations**：防止无限循环

### 4. 事件系统设计

```
AgentEventType:
  AGENT_START / AGENT_END
  TURN_START / TURN_END
  MESSAGE_START / MESSAGE_UPDATE / MESSAGE_END
  TOOL_EXECUTION_START / TOOL_EXECUTION_UPDATE / TOOL_EXECUTION_END
```

**为什么这样设计？**
- **观察者模式**：UI 可以订阅事件来实时更新
- **解耦**：Loop 不需要知道 UI 的存在，只需要发射事件
- **可扩展性**：后续可以添加日志、监控等其他监听器

### 5. 工具设计

4 个基础工具：
- `read`：读取文件
- `write`：写入文件（覆盖）
- `edit`：精确字符串替换
- `bash`：执行 bash 命令

**安全限制**：所有操作限制在 `workspace/` 目录下

**为什么这样设计？**
- **最小够用**：这 4 个工具足以完成大部分编程任务
- **安全性**：限制在 workspace 防止误操作重要文件
- **幂等性**：edit 使用精确字符串替换，避免误修改

## 这个设计如何解决问题？

| 问题 | 设计方案 | 效果 |
|------|----------|------|
| LLM 调用难 | 封装在 loop 中，用户只需 `agent.prompt()` | 简单易用 |
| 工具调用机制 | 统一的 Tool 接口 + 自动解析执行 | LLM 能自如使用工具 |
| 实时反馈 | 流式输出 + 事件系统 | 用户体验流畅 |
| 安全性 | workspace 目录限制 | 不会破坏系统 |
| 可演进性 | 分层架构 + 清晰接口 | 后续好加功能 |

## 未解决的问题（留给后续版本）

- ❌ 会话持久化（重启后消息丢失）
- ❌ 更丰富的工具集（git、搜索等）
- ❌ 错误恢复机制（工具执行失败怎么办）
- ❌ 多 Agent 协作
- ❌ ...
