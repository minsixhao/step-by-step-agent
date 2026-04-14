# v002: Basic Tools (基础工具增强版)

这是 Python Agent 学习项目的第二个版本，在 v001 基础上完善了工具集和错误处理。

## 本版本学习内容

- 完善工具集和错误处理
- 更好的用户体验

## 核心概念

- Tool 定义与注册
- Message 历史管理
- Agent 主循环（Think → Act → Observe）

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
# 编辑 .env 文件填入你的配置
```

或者直接设置环境变量：

```bash
export ANTHROPIC_AUTH_TOKEN="your-token-here"
export ANTHROPIC_BASE_URL="https://ark.cn-beijing.volces.com/api/coding"
export ANTHROPIC_MODEL="ark-code-latest"
```

## 运行方式

### 交互式运行

```bash
python run.py
```

这会启动一个交互式界面，你可以直接输入指令与 Agent 对话：

```
> 在 workspace 下创建一个 hello.py 文件
> 读取 hello.py 的内容
> quit
```

### 在代码中使用

```python
from agent import Agent

agent = Agent()

response = agent.prompt("创建一个打印 'Hello, World!' 的 Python 脚本")
print(response)
```

## 可用工具

- `read` - 读取文件内容
- `write` - 写入文件（覆盖）
- `edit` - 编辑文件（精确字符串替换）
- `bash` - 执行 bash 命令

所有工具都在 `workspace` 目录下操作。

## 项目结构

```
.
├── agent/
│   ├── __init__.py    # 模块导出
│   ├── agent.py       # Agent 主类
│   ├── loop.py        # Agent 主循环
│   ├── types.py       # 数据类型定义
│   └── tools/         # 工具实现
│       ├── __init__.py
│       ├── read.py
│       ├── write.py
│       ├── edit.py
│       └── bash.py
├── run.py             # 交互式运行脚本
├── .env.example       # 环境变量示例
├── requirements.txt
└── README.md
```

## 代码规范

- 所有代码注释使用中文
- 所有文档字符串使用中文
- 变量和函数名使用英文
