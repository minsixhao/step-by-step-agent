import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_edit(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行编辑文件操作（限制在 workspace 目录下）"""
    file_path = args.get("file_path")
    old_string = args.get("old_string")
    new_string = args.get("new_string")

    if not file_path:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text="错误: file_path 是必填参数")],
            is_error=True,
        )
    if old_string is None:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text="错误: old_string 是必填参数")],
            is_error=True,
        )
    if new_string is None:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text="错误: new_string 是必填参数")],
            is_error=True,
        )

    try:
        safe_path = get_safe_path(file_path)

        if not os.path.exists(safe_path):
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="edit",
                content=[TextContent(text=f"错误: 文件不存在: {file_path} (工作目录: {WORKSPACE_DIR})")],
                is_error=True,
            )

        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="edit",
                content=[TextContent(text="错误: 在文件中未找到 old_string")],
                is_error=True,
            )

        if content.count(old_string) > 1:
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="edit",
                content=[TextContent(text="错误: old_string 在文件中出现多次")],
                is_error=True,
            )

        new_content = content.replace(old_string, new_string)

        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text=f"成功编辑文件: {file_path} (工作目录: {WORKSPACE_DIR})")],
            details={"file_path": file_path, "safe_path": safe_path, "old_length": len(content), "new_length": len(new_content)},
        )
    except ValueError as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text=f"路径错误: {str(e)}")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="edit",
            content=[TextContent(text=f"编辑文件时出错: {str(e)}")],
            is_error=True,
        )


edit_tool = Tool(
    name="edit",
    description=f"通过替换精确的字符串匹配来编辑文件（所有文件操作都在 {WORKSPACE_DIR} 目录下）",
    parameters=ToolParameters(
        properties={
            "file_path": {
                "type": "string",
                "description": "要编辑的文件路径（相对于 workspace 目录）",
            },
            "old_string": {
                "type": "string",
                "description": "要查找并替换的精确字符串",
            },
            "new_string": {
                "type": "string",
                "description": "替换后的字符串",
            },
        },
        required=["file_path", "old_string", "new_string"],
    ),
    execute=execute_edit,
)
