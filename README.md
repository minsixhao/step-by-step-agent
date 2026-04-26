# Agent 学习项目

这是一个从 Demo 一步步演进到产品级的 Agent 学习项目，使用模型 Deepseek-v4-pro，Anthropic API 格式。

## 写在前面：
项目使用 vibe coding 开发。作者也读了几十个小时的 OpenClaw 源码，深知有多难读懂。

Agent 项目重要只是设计思路和工程细节。因此，作者会保证该 README.md，和 [docs](docs) 下的 `DEV_LOG.md` 为纯手写内容，作为开发记录，同时也会记录我个人的经验（会漏掉一些，我会尽量都记下来）。

作者也是从开源项目和实际工作中吸收经验，如果你也感兴趣 Agent 开发，欢迎提出意见与讨论！

## 版本索引

| 版本 | 目录 | 学习内容 | 状态 |
|------|------|----------|------|
| v001 | [001-minimal-agent](./001-minimal-agent) | Agent 基础架构、LLM 调用、4个基础工具（read/write/edit/bash） | ✅ 完成 |
| v002 | [002-basic-tools](./002-basic-tools/) | 完善工具集、错误处理 | ✅ 完成 |
| v003 | 003-xxx | xxx | ⏳ 待开发 |

## 如何使用

1. 直接在 `001-minimal-agent/` 等目录中查看 README.md
2. 对比两个版本：`diff -r 001-minimal-agent 002-basic-tools`

## 项目结构

```
step-by-step-agent/
├── README.md (项目介绍、版本索引)
├── 001-minimal-agent/ (版本1代码)
├── 002-basic-tools/ (版本2代码)
└── ...
```
