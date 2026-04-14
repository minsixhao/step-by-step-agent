# Python Code Agent 学习项目

这是一个从 Demo 一步步演进到企业级的 Code Agent 学习项目。

## 版本索引

| 版本 | 分支 | 学习内容 | 状态 |
|------|------|----------|------|
| v001 | [version/001-minimal-agent](tree/version/001-minimal-agent) | Agent 基础架构、LLM 调用、4个基础工具（read/write/edit/bash） | ✅ 完成 |
| v002 | [version/002-basic-tools](tree/version/002-basic-tools) | 完善工具集、错误处理 | ⏳ 待开发 |
| v003 | [version/003-session](tree/version/003-session) | 会话管理、持久化 | ⏳ 待开发 |

## 如何使用

1. 查看某个版本：`git checkout version/001-minimal-agent`
2. 在 GitHub 上直接点击分支查看代码
3. 对比两个版本：`git diff version/001-minimal-agent version/002-basic-tools`

## 学习路线

v001 最简 Agent → v002 基础工具 → v003 会话管理 → ... → v100 企业级

## 项目结构

```
main (仅文档：README、学习索引)
│
├── version/001-minimal-agent (代码)
├── version/002-basic-tools (代码)
├── version/003-session (代码)
└── ...
```

| 分支 | 用途 | 内容 |
|------|------|------|
| main | 导航页、入口 | 仅文档（README、版本索引） |
| version/001-minimal-agent | 代码版本1 | 代码 |
| version/002-basic-tools | 代码版本2 | 代码 |
| ... | ... | ... |
