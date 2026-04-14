# 学习路线图

本项目通过渐进式的版本迭代，展示如何从一个最简单的 Agent 逐步演进到企业级的 Code Agent。

## v001: Minimal Agent (最简 Agent)

**目标**: 建立最基础的 Agent 架构

**学习内容**:
- Agent 基础架构设计
- LLM API 调用封装
- 工具调用机制
- 4个基础工具:
  - `read` - 读取文件
  - `write` - 写入文件
  - `edit` - 编辑文件（字符串替换）
  - `bash` - 执行 bash 命令
- 工作区（workspace）安全限制

**核心概念**:
- Tool 定义与注册
- Message 历史管理
- Agent 主循环（Think → Act → Observe）

---

## v002: Basic Tools (基础工具)

**目标**: 完善工具集，增加健壮性

**学习内容**:
- 更多实用工具
- 完善的错误处理
- 工具参数验证
- 异步工具执行

---

## v003: Session Management (会话管理)

**目标**: 支持会话持久化

**学习内容**:
- 会话序列化/反序列化
- 会话存储
- 会话历史恢复

---

## 后续版本 (待规划)

- v004: Multi-turn Dialogue (多轮对话优化)
- v005: Context Management (上下文管理)
- v006: Memory (记忆模块)
- v007: Planning (计划能力)
- ...
