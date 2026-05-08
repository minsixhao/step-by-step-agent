import subprocess
import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_find(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行 find 查找文件（限制在 workspace 目录下）"""
    pattern = args.get("pattern")
    if not pattern:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="find",
            content=[TextContent(text="错误: pattern 是必填参数")],
            is_error=True,
        )

    try:
        # 构建 find 命令
        path = args.get("path")
        search_path = WORKSPACE_DIR
        if path:
            try:
                search_path = get_safe_path(path)
            except ValueError:
                search_path = os.path.join(WORKSPACE_DIR, path)

        file_type = args.get("type", "file")

        cmd_parts = ["find", search_path]

        # 添加类型过滤
        if file_type == "file":
            cmd_parts.extend(["-type", "f"])
        elif file_type == "dir":
            cmd_parts.extend(["-type", "d"])
        # type == "all" 时不添加类型过滤

        # 添加名称模式
        cmd_parts.extend(["-name", pattern])

        result = subprocess.run(
            " ".join(cmd_parts),
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE_DIR,
        )

        output = []
        if result.stdout:
            # 使输出路径相对于 workspace，更简洁
            lines = result.stdout.strip().split("\n")
            relative_paths = []
            for line in lines:
                if line:
                    if line.startswith(WORKSPACE_DIR):
                        rel_path = line[len(WORKSPACE_DIR):].lstrip(os.sep)
                        relative_paths.append(rel_path if rel_path else ".")
                    else:
                        relative_paths.append(line)
            output.append("\n".join(relative_paths))
        if result.stderr:
            output.append(f"标准错误输出:\n{result.stderr}")

        combined_output = "\n".join(output) if output else "未找到匹配的文件"

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="find",
            content=[TextContent(text=combined_output)],
            is_error=result.returncode != 0,
            details={"command": " ".join(cmd_parts), "return_code": result.returncode},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="find",
            content=[TextContent(text="错误: 查找在 30 秒后超时")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="find",
            content=[TextContent(text=f"查找时出错: {str(e)}")],
            is_error=True,
        )


find_tool = Tool(
    name="find",
    description=f"查找文件（所有操作都在 {WORKSPACE_DIR} 目录下）",
    is_concurrency_safe=True,  # 只读操作，可并发
    parameters=ToolParameters(
        properties={
            "pattern": {
                "type": "string",
                "description": "文件名匹配模式",
            },
            "path": {
                "type": "string",
                "description": "搜索路径，默认 workspace",
            },
            "type": {
                "type": "string",
                "description": "文件类型: file (默认), dir, all",
            },
        },
        required=["pattern"],
    ),
    execute=execute_find,
)
