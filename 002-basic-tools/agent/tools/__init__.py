"""
工具模块

包含四个核心工具：read, write, edit, bash
所有文件操作都限制在 workspace 目录下
"""

import os

# 获取 workspace 目录的绝对路径
# workspace 位于项目根目录下
_current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(os.path.dirname(_current_dir), "workspace")


def get_safe_path(file_path: str) -> str:
    """
    获取安全的文件路径，确保路径在 workspace 目录下

    Args:
        file_path: 用户提供的文件路径

    Returns:
        在 workspace 下的安全绝对路径
    """
    # 如果是绝对路径，检查是否在 workspace 下
    if os.path.isabs(file_path):
        normalized_path = os.path.normpath(file_path)
        workspace_normalized = os.path.normpath(WORKSPACE_DIR)
        if not normalized_path.startswith(workspace_normalized):
            # 如果绝对路径不在 workspace 下，将其作为相对路径处理
            file_path = file_path.lstrip(os.sep)
        else:
            return normalized_path

    # 作为相对路径，拼接在 workspace 下
    safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, file_path))

    # 再次确保路径在 workspace 下（防止 .. 攻击）
    workspace_normalized = os.path.normpath(WORKSPACE_DIR)
    if not safe_path.startswith(workspace_normalized):
        raise ValueError(f"路径 '{file_path}' 超出了 workspace 目录范围")

    return safe_path


from .read import read_tool
from .write import write_tool
from .edit import edit_tool
from .bash import bash_tool

__all__ = ["read_tool", "write_tool", "edit_tool", "bash_tool", "WORKSPACE_DIR", "get_safe_path"]
