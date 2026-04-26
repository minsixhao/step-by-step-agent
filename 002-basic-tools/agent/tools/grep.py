import subprocess
import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import get_safe_path, WORKSPACE_DIR


def execute_grep(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行 grep 搜索（限制在 workspace 目录下）"""
    pattern = args.get("pattern")
    if not pattern:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="grep",
            content=[TextContent(text="错误: pattern 是必填参数")],
            is_error=True,
        )

    try:
        # 构建 grep 命令
        cmd_parts = ["grep"]

        path = args.get("path")
        search_path = WORKSPACE_DIR
        if path:
            try:
                search_path = get_safe_path(path)
            except ValueError:
                search_path = os.path.join(WORKSPACE_DIR, path)

        output_mode = args.get("outputMode", "content")
        if output_mode == "files_with_matches":
            cmd_parts.append("-l")
        elif output_mode == "count":
            cmd_parts.append("-c")

        # 添加 grep 参数
        cmd_parts.extend(["-n", "-r"])  # 显示行号，递归搜索

        # 处理 glob 模式
        glob_pattern = args.get("glob")
        if glob_pattern:
            cmd_parts.extend(["--include", glob_pattern])

        cmd_parts.extend([pattern, search_path])

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
            output.append(result.stdout)
        if result.stderr:
            output.append(f"标准错误输出:\n{result.stderr}")

        combined_output = "\n".join(output) if output else "未找到匹配内容"

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="grep",
            content=[TextContent(text=combined_output)],
            is_error=result.returncode != 0 and result.returncode != 1,  # grep 返回 1 表示没找到，不算错误
            details={"command": " ".join(cmd_parts), "return_code": result.returncode},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="grep",
            content=[TextContent(text="错误: 搜索在 30 秒后超时")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="grep",
            content=[TextContent(text=f"搜索时出错: {str(e)}")],
            is_error=True,
        )


grep_tool = Tool(
    name="grep",
    description=f"在文件中搜索文本（所有操作都在 {WORKSPACE_DIR} 目录下）",
    parameters=ToolParameters(
        properties={
            "pattern": {
                "type": "string",
                "description": "搜索模式（正则表达式）",
            },
            "path": {
                "type": "string",
                "description": "搜索路径，默认 workspace",
            },
            "glob": {
                "type": "string",
                "description": "文件匹配模式，如 *.py",
            },
            "outputMode": {
                "type": "string",
                "description": "输出模式: content (默认), files_with_matches, count",
            },
        },
        required=["pattern"],
    ),
    execute=execute_grep,
)
