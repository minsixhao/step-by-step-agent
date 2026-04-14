# Changelog

## v001 - Minimal Agent

**初始版本 - 最简 Agent**

### 新增功能
- Agent 基础架构
- LLM API 调用封装（支持 Anthropic Claude）
- 4个基础工具:
  - `read` - 读取文件内容
  - `write` - 写入文件（覆盖）
  - `edit` - 编辑文件（精确字符串替换）
  - `bash` - 执行 bash 命令
- 工作区（workspace）安全限制
- 事件系统（订阅 Agent 执行状态）
- 流式输出支持
- 并行/串行工具执行模式

### 核心类型定义
- `Message` - 消息类型
- `Tool` - 工具定义
- `AgentState` - Agent 状态
- `AgentConfig` - Agent 配置
- `AgentEvent` - 事件系统

### 项目结构
```
agent/
├── __init__.py
├── agent.py       # Agent 主类
├── loop.py        # Agent 主循环
├── types.py       # 数据类型定义
└── tools/         # 工具实现
    ├── __init__.py
    ├── read.py
    ├── write.py
    ├── edit.py
    └── bash.py
```
