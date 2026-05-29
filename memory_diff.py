"""
Stretch goal S8 (part 2): diff two memory snapshots.

Prints ADDED / REMOVED / CHANGED memory entries between two snapshots taken with
memory_snapshot.py, with a per-file unified content diff for changed entries.

This is the demo headline: "here is exactly what the agent learned between
calls" — the institutional memory, made visible.

Usage:
    python memory_snapshot.py after_session1
    # ... run run_session_2.py ...
    python memory_snapshot.py after_session2
    python memory_diff.py after_session1 after_session2

Either argument may be a bare label (resolved to
outputs/memory_snapshot_<label>.json) or a direct path to a snapshot JSON file.
"""

import difflib
import json
import sys
from pathlib import Path

OUTPUT_DIR = Path("outputs")

# ANSI colours, disabled when output isn't a terminal (e.g. piped to a file).
_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def green(t: str) -> str:
    return _c("32", t)


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


def bold(t: str) -> str:
    return _c("1", t)


def resolve_snapshot_path(arg: str) -> Path:
    """Accept a label (after_session1) or a path (outputs/foo.json)."""
    direct = Path(arg)
    if direct.exists():
        return direct
    by_label = OUTPUT_DIR / f"memory_snapshot_{arg}.json"
    if by_label.exists():
        return by_label
    raise SystemExit(
        f"Could not find snapshot for '{arg}'. Looked for {direct} and "
        f"{by_label}. Run `python memory_snapshot.py {arg}` first."
    )


def load_snapshot(arg: str) -> dict:
    path = resolve_snapshot_path(arg)
    data = json.loads(path.read_text())
    # memory_snapshot.py writes {memories: {path: {id, content, chars}}}.
    return data.get("memories", {})


def print_content_diff(path: str, before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"a{path}",
        tofile=f"b{path}",
        lineterm="",
    )
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print("    " + green(line))
        elif line.startswith("-") and not line.startswith("---"):
            print("    " + red(line))
        elif line.startswith("@@"):
            print("    " + yellow(line))
        else:
            print("    " + line)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python memory_diff.py <before> <after>\n"
            "  e.g. python memory_diff.py after_session1 after_session2"
        )

    before_arg, after_arg = sys.argv[1], sys.argv[2]
    before = load_snapshot(before_arg)
    after = load_snapshot(after_arg)

    before_paths = set(before)
    after_paths = set(after)

    added = sorted(after_paths - before_paths)
    removed = sorted(before_paths - after_paths)
    common = sorted(before_paths & after_paths)
    changed = [p for p in common if before[p]["content"] != after[p]["content"]]

    print(bold(f"\nMemory diff: {before_arg}  ->  {after_arg}"))
    print("=" * 60)
    print(
        f"  {len(added)} added   {len(removed)} removed   "
        f"{len(changed)} changed   {len(common) - len(changed)} unchanged\n"
    )

    if added:
        print(bold(green("ADDED")))
        for path in added:
            entry = after[path]
            print(green(f"  + {path}  ({entry['chars']} chars)"))
            for line in entry["content"].splitlines():
                print("    " + green("+ " + line))
            print()

    if removed:
        print(bold(red("REMOVED")))
        for path in removed:
            entry = before[path]
            print(red(f"  - {path}  ({entry['chars']} chars)"))
            for line in entry["content"].splitlines():
                print("    " + red("- " + line))
            print()

    if changed:
        print(bold(yellow("CHANGED")))
        for path in changed:
            b_chars = before[path]["chars"]
            a_chars = after[path]["chars"]
            print(yellow(f"  ~ {path}  ({b_chars} -> {a_chars} chars)"))
            print_content_diff(path, before[path]["content"], after[path]["content"])
            print()

    if not (added or removed or changed):
        print("  (no changes - memory is identical between the two snapshots)")


if __name__ == "__main__":
    main()
