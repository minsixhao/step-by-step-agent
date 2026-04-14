import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_read(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行读取文件操作（限制在 workspace 目录下）"""
    file_path = args.get("file_path")
    if not file_path:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text="错误: file_path 是必填参数")],
            is_error=True,
        )

    try:
        safe_path = get_safe_path(file_path)

        if not os.path.exists(safe_path):
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="read",
                content=[TextContent(text=f"错误: 文件不存在: {file_path} (工作目录: {WORKSPACE_DIR})")],
                is_error=True,
            )

        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text=content)],
            details={"file_path": file_path, "safe_path": safe_path, "bytes": len(content)},
        )
    except ValueError as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text=f"路径错误: {str(e)}")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text=f"读取文件时出错: {str(e)}")],
            is_error=True,
        )


read_tool = Tool(
    name="read",
    description=f"读取文件内容（所有文件操作都在 {WORKSPACE_DIR} 目录下）",
    parameters=ToolParameters(
        properties={
            "file_path": {
                "type": "string",
                "description": "要读取的文件路径（相对于 workspace 目录）",
            }
        },
        required=["file_path"],
    ),
    execute=execute_read,
)
