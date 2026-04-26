"""
Spinner 动画组件

在后台线程运行的 spinner，用于显示工具执行状态。
"""

import time
import threading
from typing import Optional
from agent.ui.colors import Colors


class Spinner:
    """后台线程运行的 spinner"""

    # Claude Code 风格的 spinner 字符
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    INTERVAL = 0.1  # 100ms 切换一次

    def __init__(self, message: str, color: str = Colors.YELLOW):
        """
        初始化 spinner

        Args:
            message: 显示的消息，例如 "正在执行 Bash..."
            color: spinner 的颜色
        """
        self.message = message
        self.color = color
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_idx = 0
        self._start_time = time.time()

    def start(self):
        """启动 spinner 后台线程"""
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, success: Optional[bool] = None):
        """
        停止 spinner

        Args:
            success: True 显示成功状态，False 显示失败状态，None 只清除
        """
        self._running = False
        if self._thread:
            self._thread.join()
        self._final_render(success)

    def _loop(self):
        """后台循环渲染"""
        while self._running:
            self._render_frame()
            time.sleep(self.INTERVAL)

    def _render_frame(self):
        """渲染单帧：使用 \\r 回到行首覆盖"""
        frame = self.FRAMES[self._frame_idx]
        self._frame_idx = (self._frame_idx + 1) % len(self.FRAMES)
        print(
            f"{Colors.CURSOR_LINE_START}{self.color}{frame}{Colors.RESET} {self.message}",
            end="",
            flush=True,
        )

    def _final_render(self, success: Optional[bool]):
        """
        最终渲染：用成功/失败状态替换 spinner

        Args:
            success: True 显示成功，False 显示失败，None 清除行
        """
        elapsed = time.time() - self._start_time

        if success is None:
            # 只清除这一行
            print(f"{Colors.CURSOR_LINE_START}{Colors.CLEAR_LINE}", end="", flush=True)
        elif success:
            # 显示成功状态
            dot = f"{Colors.GREEN}●{Colors.RESET}"
            print(
                f"{Colors.CURSOR_LINE_START}{dot} {self.message} [{elapsed:.2f}s]{Colors.CLEAR_LINE}",
                flush=True,
            )
        else:
            # 显示失败状态
            dot = f"{Colors.RED}●{Colors.RESET}"
            print(
                f"{Colors.CURSOR_LINE_START}{dot} {self.message} [{elapsed:.2f}s]{Colors.CLEAR_LINE}",
                flush=True,
            )
