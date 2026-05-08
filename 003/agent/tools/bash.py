import subprocess
import os
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import WORKSPACE_DIR


def execute_bash(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行 bash 命令（在 workspace 目录下执行）"""
    command = args.get("command")
    if not command:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="bash",
            content=[TextContent(text="错误: command 是必填参数")],
            is_error=True,
        )

    timeout = args.get("timeout", 300)

    try:
        # 使用简单的 run 方式，先不做实时输出，避免跨平台问题
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR,
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"标准错误输出:\n{result.stderr}")

        combined_output = "\n".join(output) if output else "命令执行完成，无输出"

        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="bash",
            content=[TextContent(text=combined_output)],
            is_error=result.returncode != 0,
            details={"return_code": result.returncode, "command": command, "timeout": timeout, "cwd": WORKSPACE_DIR},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="bash",
            content=[TextContent(text=f"错误: 命令在 {timeout} 秒后超时")],
            is_error=True,
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="bash",
            content=[TextContent(text=f"执行命令时出错: {str(e)}")],
            is_error=True,
        )


bash_tool = Tool(
    name="bash",
    description=(
        f"执行 bash 命令（在 {WORKSPACE_DIR} 目录下执行）。"
        "用途：文件操作、包管理、编译检查、API 测试、数据库检查等。"
        "常用验证命令: npx tsc --noEmit / npm run build (前端编译检查)、"
        "curl (API 端点测试)、python -c '...' (数据库连接检查)、"
        "npm run dev & (启动开发服务器查看控制台报错)"
    ),
    is_concurrency_safe=False,  # 命令执行可能有副作用，不可并发
    parameters=ToolParameters(
        properties={
            "command": {
                "type": "string",
                "description": "要执行的 bash 命令",
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒），默认 300",
            },
        },
        required=["command"],
    ),
    execute=execute_bash,
)
