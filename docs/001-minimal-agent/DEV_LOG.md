---
name: 开发者日志
description: 记录本版本开发过程中的思考、决策和待解决问题
---

# 开发者日志

## 🎯 要解决的问题

### 核心问题

- 怎么实现一个最简的文件编辑 Agent，这是 OpenClaw 和任何 Coding Agent 的基础

### 参考来源

- OpenClaw 是运行在 [pi-mono](https://github.com/badlogic/pi-mono) 引擎上面的 Agent，它的创始人说，只需要四个工具就可以实现一个 Coding Agent。
- OpenClaw 架构解析见：[OpenClaw Architecture, Explained](https://ppaolo.substack.com/p/openclaw-system-architecture-overview)

## 开始

本版本的实现思路：

1. **交互式 CLI** - 最简的命令行界面，给发送指令和实时查看 Agent 执行日志
   - 启动方式 `python run.py`
   - 对应目录：[`001-minimal-agent/agent/ui/`](../../001-minimal-agent/agent/ui/)

2. **四个最简最基础工具** - `read`, `write`, `edit`, `bash`
   - 对应目录：[`001-minimal-agent/agent/tools/`](../../001-minimal-agent/agent/tools/)

3. **Agent 定义**
   - 对应文件：[`001-minimal-agent/agent/agent.py`](../../001-minimal-agent/agent/agent.py)

4. **Agent Loop** - 目前通用的 Agent 设计方式
   - 对应文件：[`001-minimal-agent/agent/loop.py`](../../001-minimal-agent/agent/loop.py)


## Agent 测试
- 见测试方案 [`TEST_PLAN`](../../001-minimal-agent/test/TEST_PLAN.md)
- 见测试结果 [`TEST_RESULT`](../../001-minimal-agent/test/TEST_RESULT.md)