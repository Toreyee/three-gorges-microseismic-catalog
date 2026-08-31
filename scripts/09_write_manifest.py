#!/usr/bin/env python3
"""Write a deterministic SHA-256 manifest for public release files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", "build", "dist"}
EXCLUDED_NAMES = {"SHA256SUMS", "regional.copy-error.bak"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("SHA256SUMS"))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path != output
        and path.name not in EXCLUDED_NAMES
        and not any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.relative_to(root).parts)
    ]
    lines = [f"{sha256(path)}  {path.relative_to(root).as_posix()}" for path in sorted(files)]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(lines)} entries to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
