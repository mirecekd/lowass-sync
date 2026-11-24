# lowass_sync/uia_probe.py
"""Explores the UI Automation tree of a running desktop app (new Outlook, Teams, ...). Run it on Windows (pip install pywinauto),
the app already running and its window visible (not minimised), from the project folder:

  python -m lowass_sync.uia_probe --list-windows                          title, class, pid and process of the top-level windows
  python -m lowass_sync.uia_probe --process olk.exe --dump --out o.txt    the control tree as indented text (--depth 40, --max-elements 20000)
  python -m lowass_sync.uia_probe --window Outlook --find meeting         path and properties of elements matching name/id/class
  python -m lowass_sync.uia_probe --process olk.exe --watch 60            ONLY the changes of the tree, with a time
  python -m lowass_sync.uia_probe --pid 1234 --dump                       choose the window by process id instead of the title regex

Chromium / WebView2 (new Outlook, new Teams) build a rich UIA tree only when they see an assistive tool. If the dump is almost
empty: run with --enable-accessibility (walks the tree once first and waits, which usually wakes it), start Narrator
(Win+Ctrl+Enter, it forces it), or start the app / browser with --force-renderer-accessibility (msedge, chrome).
Read-only: nothing is clicked or typed. A dump contains the visible texts (meeting titles): never commit it."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lowass_sync.uia.pywinauto_reader import top_windows
from lowass_sync.uia.session import count_line, settled_snapshot, watch
from lowass_sync.uia.tree import find, format_node, pick_windows, pids_by_process


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="uia_probe", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-windows", action="store_true", help="list the top-level windows and exit")
    ap.add_argument("--window", metavar="REGEX", help="choose the window whose title matches (case-insensitive)")
    ap.add_argument("--pid", type=int, help="choose the window of this process id")
    ap.add_argument("--process", metavar="NAMES", help="choose the window of the process with this executable name (comma separated, e.g. olk.exe)")
    ap.add_argument("--dump", action="store_true", help="print the control tree")
    ap.add_argument("--find", metavar="TEXT", help="print elements whose name / automation id / class contains TEXT")
    ap.add_argument("--watch", type=float, metavar="SECONDS", help="print only the tree changes for this long")
    ap.add_argument("--interval", type=float, default=0.5, help="seconds between snapshots for --watch")
    ap.add_argument("--depth", type=int, default=40, help="deepest level to read")
    ap.add_argument("--max-elements", type=int, default=20000, help="stop after this many elements (WebView2 trees are huge)")
    ap.add_argument("--out", metavar="FILE", help="write the --dump or --watch text to this UTF-8 file")
    ap.add_argument("--fields", default="name,flags", help="--watch: which properties to compare (name,class_name,rect,flags)")
    ap.add_argument("--ignore", default="call-duration|^\\[[^]]*\\] ~ .*Text\\[0\\]  name: '\\d\\d:\\d\\d'",
                    help="--watch: regex of change lines to hide (default: a running clock); empty = hide nothing")
    ap.add_argument("--enable-accessibility", action="store_true", help="walk the tree once and wait first, to wake Chromium")
    args = ap.parse_args(argv)
    if not (args.list_windows or args.dump or args.find is not None or args.watch is not None):
        ap.error("say what to do: --list-windows, --dump, --find TEXT or --watch SECONDS")
    if not args.list_windows and args.window is None and args.pid is None and args.process is None:
        ap.error("choose the window with --window REGEX, --pid N or --process NAME (see --list-windows)")
    return args


def choose(args: argparse.Namespace):
    windows = top_windows()
    if args.list_windows:
        for w, _ in windows:
            print(f"pid={w.pid:<6} {w.process:24} class={w.class_name:28} title={w.title!r}")
        return None
    chosen = pick_windows([w for w, _ in windows], args.window, args.pid)
    if args.process:
        pids = pids_by_process(chosen, args.process.split(","))
        chosen = [w for w in chosen if w.pid in pids]
    chosen.sort(key=lambda w: not w.title)  # stable: windows with a title first, an app owns many hidden ones
    if not chosen:
        raise SystemExit("no window matches; see --list-windows")
    if len(chosen) > 1:
        print(f"{len(chosen)} windows match, using the first; the others:")
        for w in chosen[1:]:
            print(f"  pid={w.pid} class={w.class_name} title={w.title!r}")
    handle = chosen[0].handle
    print(f"window: pid={chosen[0].pid} {chosen[0].process} title={chosen[0].title!r}")
    return next(info for w, info in windows if w.handle == handle)


def main(argv: list[str] | None = None) -> int:
    args = parse(argv)
    root = choose(args)
    if root is None:
        return 0
    if args.watch is not None:
        watch(root, args)
        return 0
    nodes, truncated = settled_snapshot(root, args)
    if args.find is not None:
        hits = find(nodes, args.find)
        for node in hits:
            print(format_node(node, with_path=True))
        print(f"{len(hits)} match(es) in {count_line(nodes, truncated, args.max_elements)}")
    if args.dump:
        text = "\n".join(format_node(n) for n in nodes)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        print(count_line(nodes, truncated, args.max_elements) + (f"; written to {args.out}" if args.out else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
