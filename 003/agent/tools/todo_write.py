"""
TodoWrite 工具

让 Agent 对复杂任务自我管理进度，支持两级层级、依赖关系和文件持久化。
"""

import os
import json
from typing import Optional, Callable, Any
from agent.types import Tool, ToolResult, ToolParameters, TextContent
from agent.tools import WORKSPACE_DIR

TODO_DIR = os.path.join(WORKSPACE_DIR, ".agent")
TODO_FILE = os.path.join(TODO_DIR, "todos.json")


def _collect_items(todos: list) -> list:
    """
    收集所有节点（父节点和子节点），返回 (item, path, is_leaf) 列表

    path 示例: "todos[0]", "todos[1].children[2]"
    """
    items = []
    for i, t in enumerate(todos):
        if t.get("children"):
            # 父节点有子节点 → 父节点不是叶子
            items.append((t, f"todos[{i}]", False))
            for j, child in enumerate(t["children"]):
                items.append((child, f"todos[{i}].children[{j}]", True))
        else:
            # 父节点无子节点 → 父节点本身是叶子
            items.append((t, f"todos[{i}]", True))
    return items


def _find_item_by_id(todos: list, target_id: str) -> Optional[dict]:
    """通过 id 查找节点"""
    for t in todos:
        if t.get("id") == target_id:
            return t
        if t.get("children"):
            for child in t["children"]:
                if child.get("id") == target_id:
                    return child
    return None


def _is_completed(item: dict) -> bool:
    """判断一个节点是否已完成（含子节点全部完成）"""
    if item.get("children"):
        return all(c.get("status") == "completed" for c in item["children"])
    return item.get("status") == "completed"


def _validate(todos: list) -> Optional[str]:
    """校验 todos 列表，返回错误信息或 None"""
    if not todos:
        return "任务列表不能为空。要清除列表，请将所有任务标记为 completed。"

    # ── 收集所有节点和叶子节点 ──
    all_items = _collect_items(todos)
    leaf_items = [(item, path) for item, path, is_leaf in all_items if is_leaf]

    # ── 1. 检查 ID 唯一性 ──
    seen_ids = set()
    for item, path, _ in all_items:
        item_id = item.get("id")
        if not item_id or not isinstance(item_id, str):
            return f"{path}: 缺少 id 字段或 id 不是字符串。每个任务都必须有唯一的 id（如 '1', '2.1'）。"
        if item_id in seen_ids:
            return f"id '{item_id}' 重复，{path} 的 id 必须唯一。"
        seen_ids.add(item_id)

    # ── 2. 收集所有声明的 id，用于 depends_on 引用校验 ──
    all_ids = {item.get("id") for item, _, _ in all_items}

    # ── 3. depends_on 格式与存在性校验 ──
    for item, path, _ in all_items:
        deps = item.get("depends_on", [])
        if not isinstance(deps, list):
            return f"{path}: depends_on 必须是数组。"
        for dep_id in deps:
            if not isinstance(dep_id, str):
                return f"{path}: depends_on 中的 '{dep_id}' 必须是字符串（id）。"
            if dep_id not in all_ids:
                return f"{path}: depends_on 引用了不存在的 id '{dep_id}'。"

    # ── 4. 至少一个 in_progress，允许多个独立任务并发 ──
    in_progress_leaves = [(item, path) for item, path in leaf_items if item.get("status") == "in_progress"]

    all_done = all(item.get("status") == "completed" for item, _ in leaf_items)
    if not all_done and len(in_progress_leaves) == 0:
        return "存在未完成的任务时，必须至少有一个任务处于 in_progress 状态。"

    # ── 5. 有子节点的父节点 - 状态一致性 ──
    for i, t in enumerate(todos):
        if not t.get("children"):
            continue
        children = t["children"]
        parent_status = t.get("status")

        # 父 completed → 所有子必须 completed
        if parent_status == "completed":
            for child in children:
                if child.get("status") != "completed":
                    return f"todos[{i}] 已标记 completed，但其子任务 '{child.get('id')}' 尚未完成。"

        # 父 pending → 子不能 in_progress
        if parent_status == "pending":
            for child in children:
                if child.get("status") == "in_progress":
                    return f"todos[{i}] 状态为 pending，但其子任务 '{child.get('id')}' 为 in_progress。请将父任务也设为 in_progress。"

        # 父 in_progress → 必须至少有一个子 in_progress
        if parent_status == "in_progress":
            has_in_progress_child = any(c.get("status") == "in_progress" for c in children)
            if not has_in_progress_child:
                return f"todos[{i}] 状态为 in_progress，但没有任何子任务处于 in_progress。"

    # ── 6. in_progress 节点的 depends_on 必须全部已完成 ──
    for item, path, _ in all_items:
        deps = item.get("depends_on", [])
        if item.get("status") == "in_progress" and deps:
            for dep_id in deps:
                dep_item = _find_item_by_id(todos, dep_id)
                if dep_item and not _is_completed(dep_item):
                    return f"{path} (id='{item.get('id')}') 依赖 '{dep_id}'，但 '{dep_id}' 尚未完成。请先完成依赖项。"

    return None


def _read_todos() -> list:
    """从文件读取当前 todos"""
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_todos(todos: list) -> None:
    """将 todos 写入文件"""
    os.makedirs(TODO_DIR, exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def _count_progress(todos: list) -> dict:
    """统计叶子节点级别的进度"""
    all_items = _collect_items(todos)
    leaf_items = [(item, path) for item, path, is_leaf in all_items if is_leaf]
    total = len(leaf_items)
    completed = sum(1 for item, _ in leaf_items if item.get("status") == "completed")
    in_progress = [item for item, _ in leaf_items if item.get("status") == "in_progress"]
    return {"completed": completed, "total": total, "current_task": in_progress[0] if in_progress else None, "current_tasks": in_progress}


def execute_todo_write(
    tool_call_id: str,
    args: dict,
    on_update: Optional[Callable[[Any], None]] = None,
) -> ToolResult:
    """执行 todo_write 操作"""
    todos = args.get("todos", [])

    # 1. 校验
    error = _validate(todos)
    if error:
        return ToolResult(
            tool_call_id=tool_call_id,
            tool_name="todo_write",
            content=[TextContent(text=error)],
            is_error=True,
        )

    # 2. 读取旧列表
    old_todos = _read_todos()

    # 3. 判断是否全部叶子节点完成 → 写空数组
    progress = _count_progress(todos)
    all_done = progress["total"] > 0 and progress["completed"] == progress["total"]
    new_todos = [] if all_done else todos

    # 4. 写入文件
    _write_todos(new_todos)

    # 5. 构建返回给 LLM 的引导文本
    if all_done:
        text = "所有任务已完成，任务列表已清空。请向用户总结完成的工作。"
    else:
        in_progress = progress["current_tasks"]
        if len(in_progress) == 1:
            label = in_progress[0]["activeForm"]
            current_str = f"当前正在执行: {label}。"
        else:
            labels = ", ".join(t["activeForm"] for t in in_progress)
            current_str = f"当前并发执行 {len(in_progress)} 项: {labels}。"
        text = (
            f"任务列表已更新。进度: {progress['completed']}/{progress['total']} 已完成。"
            f"{current_str}请继续实现。"
        )

    return ToolResult(
        tool_call_id=tool_call_id,
        tool_name="todo_write",
        content=[TextContent(text=text)],
        details={
            "old_todos": old_todos,
            "new_todos": new_todos,
            "completed": progress["completed"],
            "total": progress["total"],
            "current_task": progress["current_task"],
            "current_tasks": progress["current_tasks"],
            "all_done": all_done,
        },
    )


todo_write_tool = Tool(
    name="todo_write",
    description=(
        "更新任务列表，用于跟踪复杂多步任务的进度。"
        "支持两级层级（父任务含子任务）和依赖关系。"
        "规则：每个实现类父任务的最后子步骤必须是运行验证步骤（命名格式：'运行验证：xxx'），"
        "验证失败则新增修复子步骤后重新验证，不准跳过。"
        "验证步骤依赖该父任务的所有实现子步骤。"
    ),
    is_concurrency_safe=False,
    parameters=ToolParameters(
        properties={
            "todos": {
                "type": "array",
                "description": "完整的任务列表（含父子层级）。每次传入完整列表，而非仅变更项。",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "唯一标识，如 '1', '2', '2.1', '2.2'",
                        },
                        "content": {
                            "type": "string",
                            "description": "任务描述，祈使语态，例如'实现后端数据库模型'",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "任务状态",
                        },
                        "activeForm": {
                            "type": "string",
                            "description": "进行时描述，例如'正在实现数据库模型'",
                        },
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "依赖的其他任务 id 列表，被依赖任务完成后本任务才能开始",
                        },
                        "children": {
                            "type": "array",
                            "description": "子任务列表（可选），用于将大任务拆解为具体可执行的步骤",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "唯一标识，如 '1.1', '1.2', '2.1'",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "子任务描述，祈使语态",
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": ["pending", "in_progress", "completed"],
                                        "description": "子任务状态",
                                    },
                                    "activeForm": {
                                        "type": "string",
                                        "description": "进行时描述",
                                    },
                                    "depends_on": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "依赖的其他任务 id 列表",
                                    },
                                },
                                "required": ["id", "content", "status", "activeForm"],
                            },
                        },
                    },
                    "required": ["id", "content", "status", "activeForm"],
                },
            }
        },
        required=["todos"],
    ),
    execute=execute_todo_write,
)
