---
name: 开发者日志
description: 记录本版本开发过程中的思考、决策和待解决问题
---

# 开发者日志

## 🎯 目标

当前项目是在 [`001-minimal-agent`](../../001-minimal-agent/) 的基础上进行优化。它可以进行怎么优化呢？

—— 当然是工具！

我们可以先返回 [`001-minimal-agent/agent/tools`](../../001-minimal-agent/agent/tools/) 的工具定义看看可以怎么优化。


### 参考来源

- pi-mono 工具定义
- claude code 工具定义

## 💡 工具优化

### 方向1：bash 工具拆分

| 工具 | 搜索对象 | 递归 | 输出内容 | 典型使用场景 |
|------|----------|------|----------|--------------|
| `ls` | 目录项 | 否 | 文件名+详情 | 查看当前目录有什么 |
| `find` | 文件名 | 是 | 文件路径 | 找到某个文件在哪 |
| `grep` | 文件内容 | 是 | 匹配行+行号 | 找到某段代码在哪 |

### 方向2：Context Engineering
1. `read`: 添加参数 `offset`, `limit`
2. `bash`: 添加参数 `timeout`


### 其他
[`001-minimal-agent`](../../001-minimal-agent/) 设置工具调用处理上限是 20。在这个 demo 中删除。[`Agent Loop`](../../002-basic-tools/agent/loop.py) 直到模型不再调用工具时退出。

有遇到什么问题呢，token 爆炸怎么办？ —— 看下个版本

## Agent 测试
- 见测试方案 [`TEST_PLAN`](../../002-basic-tools/test/TEST_PLAN.md)
- 见测试结果 [`TEST_RESULT`](../../002-basic-tools/test/TEST_RESULT.md)