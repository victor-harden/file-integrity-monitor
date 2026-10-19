#!/usr/bin/env python3
"""Baseline and verify file integrity with SHA-256."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_EXCLUDES = [".git", "node_modules", "__pycache__", "*.log", "*.pyc"]


def sha256_file(path: Path, chunk: int = 65536) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def excluded(path: Path, root: Path, patterns) -> bool:
    relative = path.relative_to(root)
    return any(fnmatch.fnmatch(part, pattern) or fnmatch.fnmatch(relative.name, pattern)
               for part in relative.parts for pattern in patterns)


def baseline(root: Path, excludes=None) -> dict:
    patterns = excludes if excludes is not None else DEFAULT_EXCLUDES
    files = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or excluded(path, root, patterns):
            continue
        stat = path.stat()
        files[str(path.relative_to(root))] = {
            "sha256": sha256_file(path),
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }
    return {"root": str(root), "files": files}


def compare(old: dict, new: dict) -> dict:
    old_files, new_files = old.get("files", {}), new.get("files", {})
    added = sorted(set(new_files) - set(old_files))
    removed = sorted(set(old_files) - set(new_files))
    changed = sorted(path for path in set(old_files) & set(new_files)
                     if old_files[path]["sha256"] != new_files[path]["sha256"])
    return {"added": added, "removed": removed, "changed": changed,
            "clean": not (added or removed or changed)}


def render(result) -> str:
    if result["clean"]:
        return "no changes detected"
    lines = []
    for label in ("added", "removed", "changed"):
        for path in result[label]:
            lines.append(f"{label:<8} {path}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="File integrity monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("baseline")
    p.add_argument("root", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--exclude", action="append", default=[])

    p = sub.add_parser("verify")
    p.add_argument("root", type=Path)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2

    if args.command == "baseline":
        data = baseline(args.root, args.exclude or None)
        args.out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"baseline written for {len(data['files'])} files -> {args.out}")
        return 0

    try:
        old = json.loads(args.baseline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read baseline: {exc}", file=sys.stderr)
        return 2
    result = compare(old, baseline(args.root))
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
