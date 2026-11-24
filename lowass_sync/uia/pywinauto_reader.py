# lowass_sync/uia/pywinauto_reader.py
"""Windows glue of the UIA probe: reads UI Automation elements through pywinauto (imported lazily, Windows only)."""
from __future__ import annotations

from pathlib import Path

from lowass_sync.uia.tree import WindowInfo, flags_text


def desktop():
    try:
        from pywinauto import Desktop  # type: ignore[import-not-found]  # Windows only
    except ImportError as exc:
        raise SystemExit(f"pywinauto (Windows only) is not available: {exc}\nInstall it on Windows: pip install pywinauto") from exc
    return Desktop(backend="uia")


def process_get_path(pid: int) -> str:
    """Executable path of a process (kernel32, so it does not depend on the pywinauto version)."""
    import ctypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]  # Windows only
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        raise OSError(f"cannot open process {pid}")
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = ctypes.c_uint(len(buf))
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            raise OSError(f"no image name for process {pid}")
        return buf.value
    finally:
        kernel32.CloseHandle(handle)


def top_windows() -> list[tuple[WindowInfo, object]]:
    top = desktop()  # first: a missing pywinauto must give the install hint
    processes: dict[int, str] = {}
    found = []
    for wrapper in top.windows():
        info = wrapper.element_info
        pid = int(info.process_id or 0)
        if pid not in processes:
            try:
                processes[pid] = Path(process_get_path(pid)).name
            except Exception:  # noqa: BLE001 - a protected process has no readable path
                processes[pid] = "?"
        found.append((WindowInfo(int(info.handle or 0), info.name or "", info.class_name or "", pid, processes[pid]), info))
    return found


def read_element(info) -> dict:
    """Properties of one UIA element; an element that vanished while walking reads as empty."""
    try:
        r = info.rectangle
        rect = (r.left, r.top, r.right, r.bottom)
        try:
            focused = bool(info.element.CurrentHasKeyboardFocus)
        except Exception:  # noqa: BLE001
            focused = False
        return {"control_type": info.control_type or "?", "name": info.name or "", "automation_id": info.automation_id or "",
                "class_name": info.class_name or "", "rect": rect, "flags": flags_text(bool(info.enabled), focused)}
    except Exception:  # noqa: BLE001
        return {"control_type": "?", "name": "", "automation_id": "", "class_name": "", "rect": (0, 0, 0, 0), "flags": "gone"}


def children_of(info) -> list:
    try:
        return list(info.children())
    except Exception:  # noqa: BLE001
        return []
