# v001: Minimal Agent 设计文档

## 核心架构

```
┌─────────────────────────────────────┐
│   Agent (用户友好接口)               │
├─────────────────────────────────────┤
│   Loop (主循环: Think → Act → Observe) │
├─────────────────────────────────────┤
│   Types (数据模型定义)               │
├─────────────────────────────────────┤
│   Tools (4个基础工具)                │
└─────────────────────────────────────┘
```

## 关键设计

### 1. 数据模型（[types.py](../../001-minimal-agent/agent/types.py)）

- **Message**：role + content[TextContent|ToolCall|ToolResult]
- **Tool**：name + description + parameters + execute()
- **State vs Config 分离**：`AgentState`（可变）vs `AgentConfig`（不可变）
- **事件系统**：11 种事件类型，观察者模式解耦 Loop 和 UI

### 2. 主循环（[loop.py](../../001-minimal-agent/agent/loop.py)）

```
while iteration < max_iterations:
    1. 调用 LLM（流式输出）
    2. 解析响应，提取 ToolCall
    3. 执行工具（支持并行/串行）
    4. 将 ToolResult 放回消息历史
    5. 无 ToolCall 则结束
```

### 3. 4 个工具

| 工具 | 作用 |
|------|------|
| `read` | 读取文件 |
| `write` | 写入文件 |
| `edit` | 精确字符串替换 |
| `bash` | 执行命令 |

所有操作限制在 `workspace/` 目录。

### 4. 用户接口（[agent.py](../../001-minimal-agent/agent/agent.py)）

- 简洁的 `prompt()` 方法
- 事件订阅机制
- 状态管理封装
