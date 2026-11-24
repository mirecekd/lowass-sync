# lowass_sync/uia/tree.py
"""Pure logic of the UI Automation probe (no Windows imports): the Node of a UI Automation tree, its text form, the walk with a
depth and element cap, the search and the diff of two snapshots. The walk gets the element reading as functions, so it is
tested with fake elements."""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

NAME_LIMIT = 300  # a call tile or a calendar item packs several states into one long name


@dataclass(frozen=True)
class Node:
    control_type: str
    name: str
    automation_id: str
    class_name: str
    rect: tuple[int, int, int, int]  # left, top, right, bottom
    path: str  # stable key: control_type[index among same-type siblings] (+ #automation_id), joined by "/"
    depth: int = 0
    flags: str = ""  # e.g. "enabled focus"


@dataclass(frozen=True)
class WindowInfo:
    handle: int
    title: str
    class_name: str
    pid: int
    process: str


def flags_text(enabled: bool, focused: bool) -> str:
    return ("enabled" if enabled else "disabled") + (" focus" if focused else "")


def one_line(text: str, limit: int = NAME_LIMIT) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def segment(control_type: str, index: int, automation_id: str) -> str:
    return f"{control_type}[{index}]" + (f"#{automation_id}" if automation_id else "")


def format_node(node: Node, with_path: bool = False) -> str:
    """One line: indented by depth, or prefixed by the path (for --find)."""
    props = (f"name='{one_line(node.name)}' id='{node.automation_id}' class='{node.class_name[:40]}' "
             f"rect={','.join(map(str, node.rect))} [{node.flags}]")
    if with_path:
        return f"{node.path}  {node.control_type} {props}"
    return f"{'  ' * node.depth}{node.control_type} {props}"


def collect(root: Any, read: Callable[[Any], dict], children: Callable[[Any], list], max_depth: int = 12,
            max_elements: int = 5000) -> tuple[list[Node], bool]:
    """Depth-first walk in tree order. read(element) -> dict with the Node fields except path and depth. Returns the nodes
    and whether the cap of max_elements cut the walk."""
    nodes: list[Node] = []
    truncated = False
    data = read(root)
    stack = [(root, data, segment(data["control_type"], 0, data["automation_id"]), 0)]
    while stack:
        element, data, path, depth = stack.pop()
        nodes.append(Node(path=path, depth=depth, **data))
        if depth >= max_depth:
            continue
        seen: dict[str, int] = {}
        kids = []
        for kid in children(element):
            if len(nodes) + len(stack) + len(kids) >= max_elements:
                truncated = True
                break
            kid_data = read(kid)
            kind = kid_data["control_type"]
            index = seen.get(kind, 0)
            seen[kind] = index + 1
            kids.append((kid, kid_data, f"{path}/{segment(kind, index, kid_data['automation_id'])}", depth + 1))
        stack.extend(reversed(kids))
    return nodes, truncated


def matches(node: Node, text: str) -> bool:
    needle = text.lower()
    return any(needle in field.lower() for field in (node.name, node.automation_id, node.class_name))


def find(nodes: list[Node], text: str) -> list[Node]:
    return [n for n in nodes if matches(n, text)]


def diff(old: list[Node], new: list[Node], fields: tuple[str, ...] = ("name", "class_name", "rect", "flags")) -> list[str]:
    """Changes between two snapshots, keyed by Node.path: '- removed', '+ added', '~ changed field' (only the given fields)."""
    before = {n.path: n for n in old}
    after = {n.path: n for n in new}
    lines = [f"- {format_node(n, with_path=True)}" for p, n in before.items() if p not in after]
    for path, node in after.items():
        previous = before.get(path)
        if previous is None:
            lines.append(f"+ {format_node(node, with_path=True)}")
            continue
        for field in fields:
            was, now = getattr(previous, field), getattr(node, field)
            if was != now:
                lines.append(f"~ {path}  {field}: {one_line(str(was))!r} -> {one_line(str(now))!r}")
    return lines


def pick_windows(windows: list[WindowInfo], title_re: str | None = None, pid: int | None = None) -> list[WindowInfo]:
    """Windows with a title matching the regex (case-insensitive) and/or the process id; untitled ones never match a regex."""
    pattern = re.compile(title_re, re.IGNORECASE) if title_re else None
    return [w for w in windows if (pattern is None or pattern.search(w.title)) and (pid is None or w.pid == pid)]


def pids_by_process(windows: list[WindowInfo], names: Iterable[str]) -> list[int]:
    """Process ids of the running app, from its executable name (case-insensitive; the title changes with every view)."""
    wanted = {name.lower() for name in names}
    return sorted({w.pid for w in windows if w.process.lower() in wanted})
