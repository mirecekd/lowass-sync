# tests/test_uia_tree.py
"""Pure logic of the UI Automation probe (format, walk with cap, find, diff, window choice) with fake elements: no Windows."""
import pytest

from lowass_sync.uia.tree import (
    NAME_LIMIT,
    Node,
    WindowInfo,
    collect,
    diff,
    find,
    format_node,
    pick_windows,
    pids_by_process,
)
from lowass_sync.uia_probe import parse


def node(path: str, name: str = "", control_type: str = "Text", automation_id: str = "", flags: str = "enabled", depth: int = 0) -> Node:
    return Node(control_type, name, automation_id, "Chrome_Widget", (1, 2, 30, 40), path, depth, flags)


def fake_read(element: dict) -> dict:
    return {"control_type": element.get("type", "Pane"), "name": element.get("name", ""), "automation_id": element.get("id", ""),
            "class_name": "C", "rect": (0, 0, 1, 1), "flags": "enabled"}


def fake_children(element: dict) -> list:
    return element.get("kids", [])


def test_a_line_shows_the_properties_truncates_long_names_and_indents_by_depth():
    line = format_node(node("Window[0]/Text[0]", "x" * 400, automation_id="cap", depth=2))
    assert line.startswith("    Text name='" + "x" * (NAME_LIMIT - 3) + "...'")
    assert "id='cap'" in line and "class='Chrome_Widget'" in line and "rect=1,2,30,40" in line and "[enabled]" in line
    with_path = format_node(node("Window[0]/Text[0]", "hi"), with_path=True)
    assert with_path.startswith("Window[0]/Text[0]  Text name='hi'")
    assert "\n" not in format_node(node("p", "two\nlines"))


def test_the_class_name_is_cut_to_40_characters():
    long_class = Node("Pane", "", "", "C" * 60, (0, 0, 0, 0), "p")
    assert f"class='{'C' * 40}'" in format_node(long_class)


def test_the_walk_keeps_tree_order_numbers_same_type_siblings_and_stops_at_the_depth():
    tree = {"type": "Window", "kids": [{"type": "Text", "name": "a", "kids": [{"type": "Text", "name": "deep"}]},
                                       {"type": "Text", "name": "b", "id": "cap"}, {"type": "Button", "name": "mute"}]}
    nodes, truncated = collect(tree, fake_read, fake_children)
    assert not truncated
    assert [n.path for n in nodes] == ["Window[0]", "Window[0]/Text[0]", "Window[0]/Text[0]/Text[0]",
                                       "Window[0]/Text[1]#cap", "Window[0]/Button[0]"]
    assert [n.depth for n in nodes] == [0, 1, 2, 1, 1]
    shallow, _ = collect(tree, fake_read, fake_children, max_depth=1)
    assert [n.name for n in shallow] == ["", "a", "b", "mute"]


def test_the_element_cap_stops_a_huge_tree_and_says_so():
    tree = {"type": "Window", "kids": [{"type": "Text", "name": str(i)} for i in range(100)]}
    nodes, truncated = collect(tree, fake_read, fake_children, max_elements=10)
    assert len(nodes) == 10 and truncated
    nodes, truncated = collect(tree, fake_read, fake_children, max_elements=101)
    assert len(nodes) == 101 and not truncated


def test_find_matches_name_id_and_class_ignoring_case():
    nodes = [node("a", "Team Meeting"), node("b", "x", automation_id="MeetingIndicator"), node("c", "other"),
             Node("Pane", "", "", "MeetingHost", (0, 0, 0, 0), "d")]
    assert [n.path for n in find(nodes, "meeting")] == ["a", "b", "d"]
    assert find(nodes, "nothing") == []


def test_diff_reports_added_removed_and_changed_elements_and_nothing_when_equal():
    old = [node("w", "win"), node("w/t0", "Alice"), node("w/t1", "gone")]
    assert diff(old, list(old)) == []
    new = [node("w", "win"), node("w/t0", "Bob", flags="enabled focus"), node("w/t2", "new item")]
    lines = diff(old, new)
    assert any(line.startswith("- w/t1") and "gone" in line for line in lines)
    assert any(line.startswith("+ w/t2") and "new item" in line for line in lines)
    assert "~ w/t0  name: 'Alice' -> 'Bob'" in lines
    assert "~ w/t0  flags: 'enabled' -> 'enabled focus'" in lines
    assert len(lines) == 4


def test_windows_are_chosen_by_title_regex_and_or_pid():
    windows = [WindowInfo(1, "Inbox | Outlook", "OutlookWnd", 10, "olk.exe"), WindowInfo(2, "Notes", "Notepad", 11, "notepad.exe"),
               WindowInfo(3, "", "Hidden", 10, "olk.exe")]
    assert [w.handle for w in pick_windows(windows, "outlook")] == [1]
    assert [w.handle for w in pick_windows(windows, pid=10)] == [1, 3]
    assert [w.handle for w in pick_windows(windows, "outlook", 11)] == []


def test_the_probe_needs_an_action_and_a_window_except_for_the_window_list():
    with pytest.raises(SystemExit):
        parse([])
    with pytest.raises(SystemExit):
        parse(["--dump"])  # which window?
    assert parse(["--list-windows"]).list_windows
    a = parse(["--window", "Outlook", "--dump"])
    assert a.depth == 40 and a.max_elements == 20000 and a.interval == 0.5 and not a.enable_accessibility
    assert parse(["--pid", "5", "--watch", "30", "--interval", "1"]).watch == 30.0
    assert parse(["--process", "olk.exe", "--dump", "--enable-accessibility"]).process == "olk.exe"


def test_diff_compares_only_the_given_fields():
    old = [node("w/t0", "Alice")]
    moved = [Node("Text", "Alice", "", "Chrome_Widget", (9, 9, 9, 9), "w/t0", 0, "enabled")]
    assert diff(old, moved) != []
    assert diff(old, moved, ("name", "flags")) == []


def test_pids_by_process_finds_the_app_by_executable_name_not_by_title():
    windows = [WindowInfo(1, "Inbox | Outlook", "OlkWebView", 10, "olk.exe"),
               WindowInfo(2, "Calendar | Outlook", "OlkWebView", 10, "olk.exe"),
               WindowInfo(3, "Outlook - Mozilla Firefox", "MozillaWindowClass", 20, "firefox.exe"),
               WindowInfo(4, "Chat", "Chrome_WidgetWin_1", 30, "OLK.EXE")]
    assert pids_by_process(windows, ["olk.exe"]) == [10, 30]
    assert pids_by_process(windows, ("Firefox.exe", "olk.exe")) == [10, 20, 30]
    assert pids_by_process([windows[2]], ["olk.exe"]) == []
