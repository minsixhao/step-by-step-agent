"""
罗小黑 Logo 和界面装饰器

提供罗小黑主题的 ASCII 艺术 Logo 和界面边框。
"""

import os
from agent.ui.colors import Colors


def get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        size = os.get_terminal_size()
        return size.columns
    except (OSError, AttributeError):
        return 80  # 默认宽度


def get_luoxiaohei_logo() -> str:
    """
    获取小猫 ASCII 艺术 Logo

    返回:
        带有颜色的小猫 Logo 字符串
    """
    # 为了让数组内部代码更简洁易读，使用单字母变量代指颜色
    W = Colors.WHITE
    B = Colors.BLACK
    G = Colors.BRIGHT_BLACK
    E = Colors.GREEN
    N = Colors.BLUE
    R = Colors.RESET

    logo_lines = [
        f"{G}            {R}",
        f"{G}   {W}/\\{G}-{W}/{G}\\    {R}",
        f"{G}  ( {E}●{G}   {E}●{G})  {R}",
        f"{G}  (  {W}ω{G}  )   {R}",
        f"{G}  ({W}\"){G}_({W}\"){G}   {R}",
        "",
        f"",
        ""
    ]

    return "\n".join(logo_lines)


def print_top_border() -> None:
    """打印顶部边框"""
    print(f"{Colors.LUOXIAOHEI_DARK_GRAY}╭────────────────────────────────────────────────────────────────────────╮{Colors.RESET}")


def print_bottom_border() -> None:
    """打印底部边框"""
    print(f"{Colors.LUOXIAOHEI_DARK_GRAY}╰────────────────────────────────────────────────────────────────────────╯{Colors.RESET}")


def print_separator_line() -> None:
    """打印分隔线（白色细线），长度为终端宽度"""
    width = get_terminal_width()
    line = "─" * width
    print(f"{Colors.WHITE}{line}{Colors.RESET}")


if __name__ == "__main__":
    print(get_luoxiaohei_logo())
