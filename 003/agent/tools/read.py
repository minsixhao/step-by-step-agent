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
    path = args.get("path")
    if not path:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text="错误: path 是必填参数")],
            is_error=True,
        )

    try:
        safe_path = get_safe_path(path)

        if not os.path.exists(safe_path):
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="read",
                content=[TextContent(text=f"错误: 文件不存在: {path} (工作目录: {WORKSPACE_DIR})")],
                is_error=True,
            )

        with open(safe_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 处理 offset 和 limit 参数
        offset = args.get("offset", 0)
        limit = args.get("limit")

        if offset < 0:
            offset = 0

        start = offset
        if limit is not None and limit > 0:
            end = start + limit
        else:
            end = len(lines)

        selected_lines = lines[start:end]
        content = "".join(selected_lines)

        details = {
            "path": path,
            "safe_path": safe_path,
            "bytes": len(content),
            "total_lines": len(lines),
            "offset": offset,
            "limit": limit,
            "returned_lines": len(selected_lines),
        }

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="read",
            content=[TextContent(text=content)],
            details=details,
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
    description=f"读取文件内容，支持分页读取（所有文件操作都在 {WORKSPACE_DIR} 目录下）",
    is_concurrency_safe=True,  # 只读操作，可并发
    parameters=ToolParameters(
        properties={
            "path": {
                "type": "string",
                "description": "要读取的文件路径（相对于 workspace 目录）",
            },
            "offset": {
                "type": "integer",
                "description": "起始行号，从 0 开始",
            },
            "limit": {
                "type": "integer",
                "description": "读取行数限制",
            },
        },
        required=["path"],
    ),
    execute=execute_read,
)
