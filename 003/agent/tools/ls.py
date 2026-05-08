import subprocess
import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_ls(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行 ls 列出目录内容（限制在 workspace 目录下）"""
    path = args.get("path")

    try:
        target_path = WORKSPACE_DIR
        if path:
            try:
                target_path = get_safe_path(path)
            except ValueError:
                target_path = os.path.join(WORKSPACE_DIR, path)

        if not os.path.exists(target_path):
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="ls",
                content=[TextContent(text=f"错误: 路径不存在: {path or '.'} (工作目录: {WORKSPACE_DIR})")],
                is_error=True,
            )

        if not os.path.isdir(target_path):
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name="ls",
                content=[TextContent(text=f"错误: 不是目录: {path or '.'}")],
                is_error=True,
            )

        # 使用 ls -la 命令
        result = subprocess.run(
            ["ls", "-la", target_path],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=WORKSPACE_DIR,
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"标准错误输出:\n{result.stderr}")

        combined_output = "\n".join(output) if output else "目录为空"

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="ls",
            content=[TextContent(text=combined_output)],
            is_error=result.returncode != 0,
            details={"path": path, "target_path": target_path},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="ls",
            content=[TextContent(text="错误: 命令在 10 秒后超时")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="ls",
            content=[TextContent(text=f"列出目录时出错: {str(e)}")],
            is_error=True,
        )


ls_tool = Tool(
    name="ls",
    description=f"列出目录内容（所有操作都在 {WORKSPACE_DIR} 目录下）",
    is_concurrency_safe=True,  # 只读操作，可并发
    parameters=ToolParameters(
        properties={
            "path": {
                "type": "string",
                "description": "目录路径，默认 workspace",
            },
        },
        required=[],
    ),
    execute=execute_ls,
)
