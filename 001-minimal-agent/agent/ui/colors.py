"""
颜色定义

Claude Code 风格的 ANSI 颜色和符号定义。
"""


class Colors:
    """ANSI 颜色代码和符号"""

    # ==========================================
    # 基础颜色
    # ==========================================
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # ==========================================
    # 罗小黑配色 - 从原图精确提取的 RGB 颜色
    # ==========================================
    OUTLINE = "\033[38;2;58;30;18m"    # 边缘/线条深棕色
    BLACK = "\033[38;2;11;11;11m"      # 身体纯黑色
    YELLOW = "\033[38;2;253;242;204m"  # 眼睛淡黄色
    GREEN = "\033[38;2;195;204;91m"    # 耳朵内侧黄绿色
    BLUE = "\033[38;2;44;120;163m"     # 鼻子深蓝色
    TEXT_G = "\033[38;2;195;204;91m"   # 文本绿色
    TEXT_Y = "\033[38;2;253;242;204m"  # 文本黄色

    # 兼容旧名称（保留以便迁移）
    LUOXIAOHEI_OUTLINE = OUTLINE
    LUOXIAOHEI_BODY_BLACK = BLACK
    LUOXIAOHEI_EAR = GREEN
    LUOXIAOHEI_EYE = YELLOW
    LUOXIAOHEI_NOSE = BLUE
    LUOXIAOHEI_TEXT_GREEN = TEXT_G
    LUOXIAOHEI_TEXT_YELLOW = TEXT_Y

    # ==========================================
    # 语义化颜色
    # ==========================================
    FG_USER = CYAN
    FG_ASSISTANT = WHITE
    FG_TOOL = YELLOW
    FG_SUCCESS = GREEN
    FG_ERROR = RED
    FG_DIM = BRIGHT_BLACK

    # ==========================================
    # 光标控制
    # ==========================================
    CURSOR_LINE_START = "\r"
    CLEAR_LINE = "\033[K"
