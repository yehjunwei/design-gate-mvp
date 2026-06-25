#!/usr/bin/env python3
"""Design Gate MVP: low-friction workflow enforcement for Claude Code."""

from __future__ import annotations

import ast
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

STATE_DIR = ".design-gate"
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "max_function_lines": 40,
    "function_length_mode": "warn",
    "allowed_before_approval": ["docs/designs/", ".design-gate/"],
    "ignored_paths": [
        ".git/", ".design-gate/", "docs/designs/", "node_modules/",
        "vendor/", "dist/", "build/", "target/", "coverage/",
        "generated/", ".venv/", "venv/"
    ]
}

MUTATING_BASH_PATTERNS = [
    r"(^|[;&|]\s*)rm(\s|$)",
    r"(^|[;&|]\s*)mv(\s|$)",
    r"(^|[;&|]\s*)cp(\s|$)",
    r"(^|[;&|]\s*)touch(\s|$)",
    r"(^|[;&|]\s*)mkdir(\s|$)",
    r"\bsed\b[^;&|]*\s-i(?:\s|$)",
    r"\bgit\s+(apply|commit|checkout|switch|reset|restore|merge|rebase|clean|add)\b",
    r"\b(npm|pnpm|yarn)\s+(install|add|remove|update|upgrade)\b",
    r"\b(pip|pip3|uv)\s+(install|add|remove|sync)\b",
    r"\b(prettier|eslint)\b[^;&|]*--write\b",
    r"(^|[;&|]\s*)cat\b[^;&|]*>",
    r"(^|[;&|]\s*)echo\b[^;&|]*>"
]

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts",
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".go", ".rs"
}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def project_dir(payload: Optional[Dict[str, Any]] = None) -> Path:
    if payload and payload.get("cwd"):
        return Path(payload["cwd"]).resolve()
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()

def state_path(project: Path) -> Path:
    return project / STATE_DIR / STATE_FILE

def config_path(project: Path) -> Path:
    return project / STATE_DIR / CONFIG_FILE

def default_state() -> Dict[str, Any]:
    return {
        "task_id": None,
        "status": "IDLE",
        "design_document": None,
        "design_approved_at": None,
        "implementation_approved_at": None,
        "updated_at": now()
    }

def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(default)

def load_state(project: Path) -> Dict[str, Any]:
    return load_json(state_path(project), default_state())

def load_config(project: Path) -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config.update(load_json(config_path(project), {}))
    return config

def save_state(project: Path, state: Dict[str, Any]) -> None:
    path = state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def read_payload() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}

def emit_deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }, ensure_ascii=False))

def relative_path(project: Path, value: str) -> str:
    path = Path(value)
    try:
        if path.is_absolute():
            return path.resolve().relative_to(project).as_posix()
    except ValueError:
        return path.as_posix()
    return path.as_posix().lstrip("./")

def is_allowed_before_approval(rel: str, config: Dict[str, Any]) -> bool:
    return any(rel.startswith(prefix) for prefix in config["allowed_before_approval"])

def is_mutating_bash(command: str) -> bool:
    return any(re.search(pattern, command, re.I) for pattern in MUTATING_BASH_PATTERNS)

def handle_pre_tool(payload: Dict[str, Any]) -> None:
    project = project_dir(payload)
    state = load_state(project)
    config = load_config(project)
    status = state.get("status", "IDLE")

    if status in {"DESIGN_APPROVED", "IMPLEMENTATION", "AWAITING_HUMAN_REVIEW", "COMPLETED"}:
        return

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}

    if tool_name in {"Write", "Edit", "NotebookEdit"}:
        file_value = (
            tool_input.get("file_path")
            or tool_input.get("notebook_path")
            or tool_input.get("path")
            or ""
        )
        rel = relative_path(project, str(file_value))
        if not is_allowed_before_approval(rel, config):
            emit_deny(
                "Design Gate：design 尚未核准。此階段只能修改 docs/designs/ "
                "與 .design-gate/。請先完成 design document，並由 human 執行 "
                "`/design-gate:approve-design <task-id>`。"
            )
        return

    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        if is_mutating_bash(command):
            emit_deny(
                "Design Gate：design 尚未核准，因此阻擋明顯會修改 repository "
                "的 Bash command。請先完成 design approval。"
            )

def git_changed_files(project: Path) -> List[Path]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    paths: List[Path] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        path = project / raw.strip('"')
        if path.is_file():
            paths.append(path)
    return paths

def ignored(project: Path, path: Path, config: Dict[str, Any]) -> bool:
    try:
        rel = path.resolve().relative_to(project).as_posix()
    except ValueError:
        return True
    return any(rel.startswith(prefix) for prefix in config["ignored_paths"])

def python_function_issues(path: Path, limit: int) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    lines = text.splitlines()
    issues: List[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        start = node.body[0].lineno if node.body else node.lineno
        end = getattr(node, "end_lineno", node.lineno)
        count = 0

        doc_end = -1
        if node.body:
            first = node.body[0]
            value = getattr(first, "value", None)
            if isinstance(first, ast.Expr) and (
                isinstance(value, ast.Str)
                or isinstance(getattr(value, "value", None), str)
            ):
                doc_end = getattr(first, "end_lineno", first.lineno)

        for number in range(start, end + 1):
            if number <= doc_end:
                continue
            stripped = lines[number - 1].strip()
            if not stripped or stripped.startswith("#"):
                continue
            count += 1

        if count > limit:
            issues.append(
                f"{path}:{node.lineno} `{node.name}` 約 {count} 行有效邏輯，"
                f"超過建議上限 {limit} 行"
            )

    return issues

def heuristic_function_issues(path: Path, limit: int) -> List[str]:
    """Conservative warning-only heuristic for brace-based languages."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    function_start = re.compile(
        r"^\s*(?:(?:public|private|protected|static|final|async|export|"
        r"inline|virtual|override|suspend|internal|const)\s+)*"
        r"(?:fun\s+|func\s+|function\s+|"
        r"(?:[\w:<>,\[\]?*&]+\s+)+)"
        r"([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:->[^{}]+)?\s*\{"
    )

    issues: List[str] = []
    active = None

    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue

        if active is None:
            match = function_start.match(line)
            if match:
                active = {
                    "name": match.group(1),
                    "start": number,
                    "depth": line.count("{") - line.count("}"),
                    "count": 0
                }
            continue

        active["depth"] += line.count("{") - line.count("}")
        if stripped not in {"{", "}", "};"}:
            active["count"] += 1

        if active["depth"] <= 0:
            if active["count"] > limit:
                issues.append(
                    f"{path}:{active['start']} `{active['name']}` 約 "
                    f"{active['count']} 行有效邏輯，超過建議上限 {limit} 行"
                )
            active = None

    return issues

def collect_warnings(project: Path, config: Dict[str, Any]) -> List[str]:
    limit = int(config.get("max_function_lines", 40))
    warnings: List[str] = []

    for path in git_changed_files(project):
        if ignored(project, path, config) or path.suffix not in SOURCE_EXTENSIONS:
            continue

        if path.suffix == ".py":
            warnings.extend(python_function_issues(path, limit))
        else:
            warnings.extend(heuristic_function_issues(path, limit))

    return warnings

def handle_stop(payload: Dict[str, Any]) -> None:
    if payload.get("stop_hook_active"):
        return

    project = project_dir(payload)
    state = load_state(project)
    status = state.get("status", "IDLE")

    if status not in {"DESIGN_APPROVED", "IMPLEMENTATION"}:
        return

    config = load_config(project)
    warnings = collect_warnings(project, config)

    state["status"] = "AWAITING_HUMAN_REVIEW"
    save_state(project, state)

    warning_text = ""
    if warnings:
        warning_text = (
            "\n\nFunction length warnings：\n- "
            + "\n- ".join(warnings[:20])
            + "\n請依 responsibility 拆分，或確認 design 中已有合理 exception。"
        )

    print(json.dumps({
        "decision": "block",
        "reason": (
            "Implementation 尚未完成 human review。請顯示實際 diff、validation "
            "結果、design deviation 與 review checklist，要求 human 查看 `git diff`，"
            "然後由 human 執行 `/design-gate:approve-implementation <task-id>`。"
            + warning_text
        )
    }, ensure_ascii=False))

def normalize_task_id(raw: str) -> str:
    task = raw.strip().split()[0] if raw.strip() else ""
    if not task or not re.fullmatch(r"[A-Za-z0-9._-]+", task):
        raise ValueError("請提供只包含英數字、dot、underscore 或 hyphen 的 task ID。")
    return task

def find_design_document(project: Path, task_id: str) -> Path:
    design_dir = project / "docs" / "designs"
    candidates = sorted(design_dir.glob(f"{task_id}-*.md"))
    candidates += sorted(design_dir.glob(f"{task_id}.md"))
    if not candidates:
        raise FileNotFoundError(
            f"找不到 {task_id} 的 design document；預期路徑為 "
            f"docs/designs/{task_id}-<name>.md"
        )
    return candidates[0]

def approve_design(project: Path, raw_task: str) -> None:
    task_id = normalize_task_id(raw_task)
    document = find_design_document(project, task_id)
    state = load_state(project)
    state.update({
        "task_id": task_id,
        "status": "DESIGN_APPROVED",
        "design_document": document.relative_to(project).as_posix(),
        "design_approved_at": now(),
        "implementation_approved_at": None
    })
    save_state(project, state)
    print(f"Design approved：{task_id} ({state['design_document']})")

def approve_implementation(project: Path, raw_task: str) -> None:
    task_id = normalize_task_id(raw_task)
    state = load_state(project)

    if state.get("task_id") != task_id:
        raise ValueError(
            f"目前 active task 是 {state.get('task_id')!r}，不是 {task_id!r}。"
        )

    if state.get("status") != "AWAITING_HUMAN_REVIEW":
        raise ValueError(
            "Implementation 只能從 AWAITING_HUMAN_REVIEW 核准；"
            f"目前狀態為 {state.get('status')}。"
        )

    state["status"] = "COMPLETED"
    state["implementation_approved_at"] = now()
    save_state(project, state)
    print(f"Implementation approved：{task_id}")

def init_project(project: Path) -> None:
    (project / STATE_DIR).mkdir(parents=True, exist_ok=True)
    (project / "docs" / "designs").mkdir(parents=True, exist_ok=True)

    if not config_path(project).exists():
        config_path(project).write_text(
            json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

    if not state_path(project).exists():
        save_state(project, default_state())

    print(f"Design Gate initialized：{project}")

def check(project: Path) -> int:
    config = load_config(project)
    warnings = collect_warnings(project, config)

    if warnings:
        print("Design Gate warnings：")
        for warning in warnings:
            print(f"- {warning}")
        return 0

    print("Design Gate check passed，沒有發現 function length warning。")
    return 0

def main(argv: Sequence[str]) -> int:
    command = argv[1] if len(argv) > 1 else ""

    hook_commands = {"pre-tool", "stop"}
    payload = read_payload() if command in hook_commands else {}
    project = project_dir(payload)

    try:
        if command == "pre-tool":
            handle_pre_tool(payload)
        elif command == "stop":
            handle_stop(payload)
        elif command == "approve-design":
            approve_design(project, " ".join(argv[2:]))
        elif command == "approve-implementation":
            approve_implementation(project, " ".join(argv[2:]))
        elif command == "init":
            init_project(project)
        elif command == "check":
            return check(project)
        elif command == "status":
            print(json.dumps(load_state(project), ensure_ascii=False, indent=2))
        elif command == "reset":
            save_state(project, default_state())
            print("Design Gate state reset。")
        else:
            print(
                "Usage: design_gate.py "
                "{init|status|check|approve-design TASK|"
                "approve-implementation TASK|reset}",
                file=sys.stderr
            )
            return 2
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
