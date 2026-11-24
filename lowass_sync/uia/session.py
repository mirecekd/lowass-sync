# lowass_sync/uia/session.py
"""Snapshots of one window for the UIA probe: the walk (with the Chromium wake-up) and the --watch loop."""
from __future__ import annotations

import argparse
import re
import time

from lowass_sync.uia.pywinauto_reader import children_of, read_element
from lowass_sync.uia.tree import Node, collect, diff

WARM_UP_SECONDS = 2.0
MANY_CHANGES = 40
SMALL_TREE = 30
ACCESSIBILITY_NOTE = ("note: the tree is small. Chromium/WebView2 exposes its content only to an assistive tool: try "
                      "--enable-accessibility, Narrator running, or --force-renderer-accessibility on the app.")


def snapshot(root, args: argparse.Namespace) -> tuple[list[Node], bool]:
    return collect(root, read_element, children_of, args.depth, args.max_elements)


def settled_snapshot(root, args: argparse.Namespace) -> tuple[list[Node], bool]:
    if args.enable_accessibility:
        print("--enable-accessibility: walking the tree once and waiting to wake Chromium/WebView2 ...")
        snapshot(root, args)
        time.sleep(WARM_UP_SECONDS)
    nodes, truncated = snapshot(root, args)
    if len(nodes) < SMALL_TREE and not args.enable_accessibility:
        print(ACCESSIBILITY_NOTE)
    return nodes, truncated


def count_line(nodes: list[Node], truncated: bool, cap: int) -> str:
    return f"{len(nodes)} elements" + (f" (cut at --max-elements {cap}; raise it or lower --depth)" if truncated else "")


def watch(root, args: argparse.Namespace) -> None:
    """Prints only changes of --fields (default name and flags: the rectangles move all the time), minus lines matching --ignore."""
    previous, _ = settled_snapshot(root, args)
    fields = tuple(args.fields.split(","))
    ignore = re.compile(args.ignore) if args.ignore else None
    try:
        log = open(args.out, "w", encoding="utf-8") if args.out else None  # noqa: SIM115 - closed in finally
    except OSError as exc:
        raise SystemExit(f"cannot write {args.out}: {exc}") from exc
    print(f"watching {args.watch:.0f} s every {args.interval} s, baseline {len(previous)} elements; only changes follow (Ctrl+C ends)")
    end = time.monotonic() + args.watch
    try:
        while time.monotonic() < end:
            time.sleep(args.interval)
            current, _ = snapshot(root, args)
            stamp = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03}"
            lines = [x for x in diff(previous, current, fields) if not (ignore and ignore.search(x))]
            previous = current
            if len(lines) > MANY_CHANGES:  # minimised / restored window: the whole tree is added or removed
                lines = [f"{len(lines)} changes at once (window minimised, restored or the page changed): not listed"]
            for line in lines:
                text = f"[{stamp}] {line}"
                print(text)
                if log:
                    log.write(text + "\n")
                    log.flush()
    except KeyboardInterrupt:
        print("stopped")
    finally:
        if log:
            log.close()
