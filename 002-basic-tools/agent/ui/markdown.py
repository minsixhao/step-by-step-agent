"""
Markdown 渲染器

将 Markdown 文本渲染为终端友好的格式，使用 Unicode 字符模拟。
"""

import re
from typing import List
from agent.ui.colors import Colors


class MarkdownRenderer:
    """将 Markdown 渲染为终端友好的格式"""

    def render(self, text: str) -> str:
        """
        入口方法，按顺序应用所有渲染规则

        Args:
            text: 原始 Markdown 文本

        Returns:
            渲染后的终端友好文本
        """
        if not text:
            return text

        result = text
        result = self._render_code_blocks(result)
        result = self._render_headers(result)
        result = self._render_lists(result)
        result = self._render_inline_code(result)
        result = self._render_bold_italic(result)
        result = self._render_links(result)
        result = self._render_blockquotes(result)
        result = self._render_horizontal_rules(result)
        return result

    def _render_headers(self, text: str) -> str:
        """渲染标题"""
        lines = text.split("\n")
        result: List[str] = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2).strip()

                if level == 1:
                    border = "━" * (len(content) + 4)
                    result.append(f"{Colors.BOLD}{Colors.CYAN}{border}{Colors.RESET}")
                    result.append(f"{Colors.BOLD}{Colors.CYAN}  {content}  {Colors.RESET}")
                    result.append(f"{Colors.BOLD}{Colors.CYAN}{border}{Colors.RESET}")
                elif level == 2:
                    border = "─" * (len(content) + 2)
                    result.append(f"{Colors.BOLD}{Colors.BLUE}{border}{Colors.RESET}")
                    result.append(f"{Colors.BOLD}{Colors.BLUE} {content} {Colors.RESET}")
                else:
                    result.append(f"{Colors.BOLD}{Colors.MAGENTA}▶ {content}{Colors.RESET}")
            else:
                result.append(line)

        return "\n".join(result)

    def _render_lists(self, text: str) -> str:
        """渲染列表"""
        lines = text.split("\n")
        result: List[str] = []

        for line in lines:
            unordered_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            if unordered_match:
                indent = unordered_match.group(1)
                content = unordered_match.group(2)
                result.append(f"{indent}{Colors.YELLOW}•{Colors.RESET} {content}")
                continue

            ordered_match = re.match(r"^(\s*)(\d+)\.\s+(.+)$", line)
            if ordered_match:
                indent = ordered_match.group(1)
                num = ordered_match.group(2)
                content = ordered_match.group(3)
                result.append(f"{indent}{Colors.CYAN}{num}.{Colors.RESET} {content}")
                continue

            result.append(line)

        return "\n".join(result)

    def _render_code_blocks(self, text: str) -> str:
        """渲染代码块"""
        parts: List[str] = []
        last_end = 0
        pattern = re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL)

        for match in pattern.finditer(text):
            parts.append(text[last_end : match.start()])
            lang = match.group(1) or "code"
            code = match.group(2).rstrip()
            code_lines = code.split("\n")
            max_width = max(len(line) for line in code_lines) if code_lines else 0
            max_width = max(max_width, len(lang) + 4)

            top_border = f"{Colors.DIM}┌{'─' * (max_width + 2)}┐{Colors.RESET}"
            bottom_border = f"{Colors.DIM}└{'─' * (max_width + 2)}┘{Colors.RESET}"
            parts.append(top_border)

            if lang:
                lang_line = f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}{Colors.MAGENTA}{lang}{Colors.RESET}{' ' * (max_width - len(lang))} {Colors.DIM}│{Colors.RESET}"
                parts.append(lang_line)
                separator = f"{Colors.DIM}├{'─' * (max_width + 2)}┤{Colors.RESET}"
                parts.append(separator)

            for line in code_lines:
                padded_line = line.ljust(max_width)
                parts.append(
                    f"{Colors.DIM}│{Colors.RESET} {Colors.GREEN}{padded_line}{Colors.RESET} {Colors.DIM}│{Colors.RESET}"
                )

            parts.append(bottom_border)
            last_end = match.end()

        parts.append(text[last_end:])
        return "\n".join(parts)

    def _render_inline_code(self, text: str) -> str:
        """渲染行内代码"""
        def replace_func(match: re.Match) -> str:
            code = match.group(1)
            return f"{Colors.GREEN}`{code}`{Colors.RESET}"
        return re.sub(r"`([^`]+)`", replace_func, text)

    def _render_bold_italic(self, text: str) -> str:
        """渲染粗体和斜体"""
        def bold_replace(match: re.Match) -> str:
            content = match.group(1) or match.group(2)
            return f"{Colors.BOLD}{content}{Colors.RESET}"
        text = re.sub(r"\*\*([^*]+)\*\*|__([^_]+)__", bold_replace, text)

        def italic_replace(match: re.Match) -> str:
            content = match.group(1) or match.group(2)
            return f"{content}"  # 终端斜体支持不好，直接返回文本
        text = re.sub(r"\*([^*]+)\*|_([^_]+)_", italic_replace, text)

        return text

    def _render_links(self, text: str) -> str:
        """渲染链接"""
        def replace_func(match: re.Match) -> str:
            link_text = match.group(1)
            url = match.group(2)
            return f"{Colors.CYAN}{link_text}{Colors.RESET} ({Colors.BLUE}{url}{Colors.RESET})"
        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_func, text)

    def _render_blockquotes(self, text: str) -> str:
        """渲染引用块"""
        lines = text.split("\n")
        result: List[str] = []

        for line in lines:
            quote_match = re.match(r"^(>\s*)+(.+)$", line)
            if quote_match:
                content = quote_match.group(2)
                result.append(f"{Colors.DIM}│{Colors.RESET} {content}")
            else:
                result.append(line)

        return "\n".join(result)

    def _render_horizontal_rules(self, text: str) -> str:
        """渲染水平分隔线"""
        lines = text.split("\n")
        result: List[str] = []

        for line in lines:
            if re.match(r"^\s*[-*_]{3,}\s*$", line):
                result.append(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
            else:
                result.append(line)

        return "\n".join(result)
