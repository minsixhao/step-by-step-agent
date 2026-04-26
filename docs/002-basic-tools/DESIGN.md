# v002: Basic Tools 设计文档

## 核心架构

保持 v001 的分层架构不变：

```
┌─────────────────────────────────────┐
│   Agent (用户友好接口)               │
├─────────────────────────────────────┤
│   Loop (主循环)                      │
├─────────────────────────────────────┤
│   Types (数据模型定义)               │
├─────────────────────────────────────┤
│   Tools (7个工具实现)                │
└─────────────────────────────────────┘
```

## 关键设计决策

### 1. 保持 Tool 定义最简
- 字段：name, description, parameters, execute
- 不添加 label, renderCall 等 UI 相关字段（YAGNI）

### 2. 统一使用短参数名
- `path` 而非 `file_path`
- 与参考表保持一致

### 3. 新增工具直接调用系统命令
- grep, find, ls 直接调用系统命令
- 简单可靠，功能强大

## 7 个工具参数设计

| 工具 | 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| read | path | string | 是 | 文件路径 |
| | offset | integer | 否 | 起始行号（从 0 开始） |
| | limit | integer | 否 | 读取行数限制 |
| write | path | string | 是 | 文件路径 |
| | content | string | 是 | 要写入的内容 |
| edit | path | string | 是 | 文件路径 |
| | oldString | string | 是 | 要替换的字符串 |
| | newString | string | 是 | 替换后的字符串 |
| bash | command | string | 是 | 要执行的命令 |
| | timeout | integer | 否 | 超时时间（秒），默认 300 |
| grep | pattern | string | 是 | 搜索模式（正则表达式） |
| | path | string | 否 | 搜索路径，默认 workspace |
| | glob | string | 否 | 文件匹配模式，如 "*.py" |
| | outputMode | string | 否 | 输出模式: content/files_with_matches/count |
| find | pattern | string | 是 | 文件名匹配模式 |
| | path | string | 否 | 搜索路径，默认 workspace |
| | type | string | 否 | 文件类型: file/dir/all |
| ls | path | string | 否 | 目录路径，默认 workspace |

## 组件职责

- **types.py**: 保持不变，Tool 数据类无需修改
- **tools/read.py, write.py, edit.py, bash.py**: 更新参数名和 schema
- **tools/grep.py, find.py, ls.py**: 新增工具实现
- **tools/__init__.py**: 导出所有 7 个工具
