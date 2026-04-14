#!/usr/bin/env python3
"""
Python Agent 交互式运行脚本

使用方法：
1. 设置环境变量或配置 .env 文件
2. 运行: python run.py
3. 输入指令与 Agent 交互
4. 输入 'quit' 或 'exit' 退出
5. 输入 'reset' 重置对话历史
"""

import sys
import os

# 尝试加载 .env 文件（如果存在）
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from agent import Agent
from agent.tools import WORKSPACE_DIR
from agent.types import AgentEvent, AgentEventType, TextContent, ToolCall


def simple_display(event: AgentEvent):
    """简单的事件显示"""
    if event.type == AgentEventType.MESSAGE_UPDATE:
        if event.delta:
            print(event.delta, end="", flush=True)
    elif event.type == AgentEventType.TOOL_EXECUTION_START:
        print(f"\n[调用工具: {event.tool_name}]", flush=True)
    elif event.type == AgentEventType.TOOL_EXECUTION_END:
        if event.result and event.result.content:
            text = "\n".join(c.text for c in event.result.content)
            if event.is_error:
                print(f"[错误: {text}]", flush=True)


def main():
    print("=" * 50)
    print("Python Agent")
    print("=" * 50)
    print(f"工作目录: {WORKSPACE_DIR}")
    print()
    print("指令:")
    print("  输入你的问题/任务")
    print("  quit/exit - 退出")
    print("  reset     - 重置对话")
    print("=" * 50)
    print()

    try:
        agent = Agent()
    except ValueError as e:
        print(f"错误: {e}")
        print()
        print("请设置环境变量 ANTHROPIC_AUTH_TOKEN 或创建 .env 文件")
        print("参考 .env.example 文件了解所需配置")
        sys.exit(1)

    agent.subscribe(simple_display)

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("再见！")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print("对话已重置")
            continue

        try:
            response = agent.prompt(user_input)
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
