#!/usr/bin/env python3
"""
罗小黑 Agent 交互式运行脚本

使用方法：
1. 设置环境变量或配置 .env 文件
2. 运行: python run.py
3. 输入指令与 Agent 交互
4. 输入 '/exit' 退出
5. 输入 '/new' 重置对话历史
"""

import sys
import os
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

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
from agent.ui import TerminalRenderer
from agent.ui.logo import get_luoxiaohei_logo, print_separator_line, get_terminal_width
from agent.ui.colors import Colors


def visible_length(s: str) -> int:
    """计算 ANSI 转义序列之外的可见字符长度（考虑中文字符宽度）"""
    ansi_escape = re.compile(r'\x1b[^m]*m')
    clean_text = ansi_escape.sub('', s)
    # 计算显示宽度：中文字符占2个宽度，ASCII字符占1个宽度
    width = 0
    for char in clean_text:
        if ord(char) > 127:  # 非ASCII字符（包括中文）
            width += 2
        else:
            width += 1
    return width


def get_last_n_parts(path: str, n: int = 3) -> str:
    """获取路径的最后 n 级"""
    parts = os.path.normpath(path).split(os.sep)
    # 过滤掉空字符串
    parts = [p for p in parts if p]
    if len(parts) <= n:
        return path
    # 取最后 n 级，并加上省略号前缀
    return os.path.join("...", *parts[-n:])


def truncate_to_visible_width(text: str, max_width: int) -> str:
    """将文本截断到指定可见宽度"""
    # 先尝试简单截断
    while visible_length(text) > max_width and len(text) > 4:
        text = "..." + text[4:]
    return text


def create_input_session():
    """创建支持 Alt+Enter/Option+Enter 换行的输入会话"""
    kb = KeyBindings()
    
    @kb.add('enter')
    def _(event):
        """回车键：提交输入"""
        event.current_buffer.validate_and_handle()
    
    @kb.add('escape', 'enter')  # Alt+Enter / Option+Enter：换行
    def _(event):
        """Alt+Enter (Win/Linux) 或 Option+Enter (Mac)：插入换行"""
        event.current_buffer.insert_text('\n')
    
    session = PromptSession(
        key_bindings=kb,
        multiline=True,
        prompt_continuation=lambda width, line_number, is_soft_wrap: FormattedText([
            ('class:continuation', '│ ')
        ])
    )
    
    return session


def print_workspace_info(workspace_display: str) -> None:
    """打印工作目录信息（左对齐显示）"""
    text = f"工作目录: {workspace_display}"
    line = f"{Colors.DIM}{text}{Colors.RESET}"
    print(line)


def print_command_bar() -> None:
    """打印底部命令提示栏"""
    terminal_width = get_terminal_width()
    
    left_text = "/exit 退出 | /new 新对话"
    right_text = "Option+Enter 换行 | Enter 提交"
    
    # 计算可见长度
    visible_left = visible_length(left_text)
    visible_right = visible_length(right_text)
    
    # 计算间距
    spacing = terminal_width - visible_left - visible_right
    if spacing < 1:
        spacing = 1
    
    # 构建完整的一行
    line = f"{Colors.DIM}{left_text}{' ' * spacing}{right_text}{Colors.RESET}"
    
    # 打印
    sys.stdout.write(line)
    sys.stdout.flush()


def print_status_bar(workspace_display: str) -> None:
    """打印状态栏，左对齐命令提示，右对齐工作目录，保证在一行内"""
    terminal_width = get_terminal_width()

    left_text = "/exit 退出 | /new 新对话"
    right_prefix = "工作目录: "

    # 计算可见长度（考虑中文字符宽度）
    visible_left = visible_length(left_text)
    visible_right_prefix = visible_length(right_prefix)

    # 计算路径可用的最大宽度
    min_spacing = 1  # 左右文本之间的最小间距（减小间距）
    max_path_width = terminal_width - visible_left - visible_right_prefix - min_spacing

    # 如果路径太长，从左侧截断它
    if max_path_width > 3:  # 至少能显示 "..."
        path_visible_len = visible_length(workspace_display)
        if path_visible_len > max_path_width:
            # 从左侧截断路径，保留右侧部分
            # 逐字符截断直到长度合适
            truncated = workspace_display
            while visible_length(truncated) > max_path_width - 3 and len(truncated) > 0:
                truncated = truncated[1:]
            workspace_display = "..." + truncated
    else:
        # 终端太窄，只显示省略号
        workspace_display = "..."

    right_text = right_prefix + workspace_display
    visible_right = visible_length(right_text)

    # 计算间距（确保总宽度不超过终端宽度）
    spacing = terminal_width - visible_left - visible_right
    if spacing < 0:
        # 如果还是太长，继续截断路径
        excess = -spacing
        truncated = workspace_display
        while visible_length(truncated) > 3 and excess > 0:
            truncated = truncated[1:]
            excess -= 1
        workspace_display = "..." + truncated[3:] if len(truncated) > 3 else "..."
        right_text = right_prefix + workspace_display
        visible_right = visible_length(right_text)
        spacing = terminal_width - visible_left - visible_right
    
    if spacing < 1:
        spacing = 1

    # 构建完整的一行
    line = f"{Colors.DIM}{left_text}{' ' * spacing}{right_text}{Colors.RESET}"

    # 打印，确保不换行
    sys.stdout.write(line)
    sys.stdout.flush()


def main():
    # 打印罗小黑 Logo
    print()
    print(get_luoxiaohei_logo())
    
    try:
        agent = Agent()
    except ValueError as e:
        print(f"错误: {e}")
        print()
        print("请设置环境变量 ANTHROPIC_AUTH_TOKEN 或创建 .env 文件")
        print("参考 .env.example 文件了解所需配置")
        sys.exit(1)

    renderer = TerminalRenderer()
    agent.subscribe(renderer)

    # 只显示最近3级工作目录
    workspace_display = get_last_n_parts(WORKSPACE_DIR, 3)

    # 打印工作目录信息
    print()
    print_workspace_info(workspace_display)

    # 创建输入会话
    session = create_input_session()

    while True:
        try:
            print()
            # 打印命令提示栏（在输入前显示）
            print_command_bar()
            print()

            # 定义样式
            input_style = Style.from_dict({
                'prompt': '#00ff87',  # 罗小黑绿色
                'continuation': '#00ff87',
            })

            # 使用 prompt_toolkit 获取输入（支持 Option+Enter / Alt+Enter 换行）
            prompt_text = FormattedText([
                ('class:prompt', '❯ ')
            ])

            user_input = session.prompt(
                prompt_text,
                style=input_style
            ).strip()

            # 打印底部横线
            print_separator_line()
            
        except KeyboardInterrupt:
            print()
            print("\n再见！")
            break
        except EOFError:
            print()
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "quit", "exit"):
            print("再见！")
            break

        if user_input.lower() in ("/new", "reset"):
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
