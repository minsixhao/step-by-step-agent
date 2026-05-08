import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_write(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行写入文件操作（限制在 workspace 目录下）"""
    path = args.get("path")
    content = args.get("content", "")

    if not path:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="write",
            content=[TextContent(text="错误: path 是必填参数")],
            is_error=True,
        )

    try:
        safe_path = get_safe_path(path)

        directory = os.path.dirname(safe_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="write",
            content=[TextContent(text=f"成功写入文件: {path} (工作目录: {WORKSPACE_DIR})")],
            details={"path": path, "safe_path": safe_path, "bytes": len(content)},
        )
    except ValueError as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="write",
            content=[TextContent(text=f"路径错误: {str(e)}")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="write",
            content=[TextContent(text=f"写入文件时出错: {str(e)}")],
            is_error=True,
        )


write_tool = Tool(
    name="write",
    description=f"写入内容到文件，如果文件存在则覆盖（所有文件操作都在 {WORKSPACE_DIR} 目录下）",
    is_concurrency_safe=False,  # 写入操作，不可并发
    parameters=ToolParameters(
        properties={
            "path": {
                "type": "string",
                "description": "要写入的文件路径（相对于 workspace 目录）",
            },
            "content": {
                "type": "string",
                "description": "要写入文件的内容",
            },
        },
        required=["path", "content"],
    ),
    execute=execute_write,
)
