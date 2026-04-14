# Python Code Agent 学习项目

这是一个从 Demo 一步步演进到企业级的 Code Agent 学习项目。

## 版本索引

| 版本 | 目录 | 学习内容 | 状态 |
|------|------|----------|------|
| v001 | [001-minimal-agent](./001-minimal-agent) | Agent 基础架构、LLM 调用、4个基础工具（read/write/edit/bash） | ✅ 完成 |
| v002 | 002-basic-tools | 完善工具集、错误处理 | ⏳ 待开发 |
| v003 | 003-session | 会话管理、持久化 | ⏳ 待开发 |

## 如何使用

1. 直接在 `001-minimal-agent/` 等目录中查看对应版本的代码
2. 对比两个版本：`diff -r 001-minimal-agent 002-basic-tools`

## 学习路线

001 最简 Agent → 002 基础工具 → 003 会话管理 → ... → 100 企业级

## 项目结构

```
step-by-step-agent/
├── README.md (项目介绍、版本索引)
├── 001-minimal-agent/ (版本1代码)
├── 002-basic-tools/ (版本2代码)
├── 003-session/ (版本3代码)
└── ...
```
