#!/usr/bin/env python3
"""Verify expected inference checkpoints, hashes, and optional TorchScript readability."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

MODELS = ("eqt", "rnn", "unet", "lppnl")
KNOWN_SHA256 = {
    "diting": {
        "eqt": {
            "jit": "0951EA097CA23953D0BC74059738DCCBB4892A096FE6E44555EF378C674CADAA",
            "pt": "EE8BDD1B892F20C019934459C94CDA105D5C7FD489DD2E9EAED96D76CA803EBC",
        },
        "rnn": {
            "jit": "04399FDD925D7C779A8FC8D94DCD5E01D406D037CC076C4A580CBE5ED129C784",
            "pt": "FEFD44008FB36D919089A6148AF5EC435628CD8C172823479586A197BFD7AD07",
        },
        "unet": {
            "jit": "5CA74668292BC81DBB8BCB5497A73EC8EB7ACBFFE963AA1A5A4E7A1F27CFE561",
            "pt": "B78ACB9EEA703E634AF00117E83A3B72958BF0F9D0773048432E283E90AF0E61",
        },
        "lppnl": {
            "jit": "CCF823196E280D4387F48C6361A2ED3D2F4F87A86304CF1F96F13918718B7A0C",
            "pt": "CE83EB50EF79666A7CEB40CB3E44FD90A7E136192018B0AF0D4490E742CC4550",
        },
    }
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def check_file(path: Path, expected: str | None = None) -> bool:
    if not path.is_file():
        print(f"[MISSING] {path}")
        return False
    if path.stat().st_size == 0:
        print(f"[EMPTY] {path}")
        return False
    digest = sha256(path)
    if expected is not None and digest != expected:
        print(f"[HASH-MISMATCH] {path.name} expected={expected} actual={digest}")
        return False
    print(f"[OK] {path.name} size={path.stat().st_size} sha256={digest}")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--prefix", default="diting")
    p.add_argument("--check-companion-pt", action="store_true", help="also require/check matching .pt files")
    p.add_argument("--load", action="store_true", help="also load each .jit with torch.jit.load")
    p.add_argument("--skip-known-hash-check", action="store_true", help="do not compare against built-in release hashes")
    args = p.parse_args()

    known = None if args.skip_known_hash_check else KNOWN_SHA256.get(args.prefix)
    jit_paths: list[Path] = []
    ok = True

    for model in MODELS:
        expected = known.get(model, {}).get("jit") if known else None
        path = args.model_dir / f"{args.prefix}.{model}.jit"
        ok = check_file(path, expected) and ok
        if path.is_file():
            jit_paths.append(path)

        if args.check_companion_pt:
            expected_pt = known.get(model, {}).get("pt") if known else None
            pt = args.model_dir / f"{args.prefix}.{model}.pt"
            ok = check_file(pt, expected_pt) and ok

    if not ok:
        return 2

    if args.load:
        try:
            import torch
        except ModuleNotFoundError as exc:
            raise SystemExit("--load requires torch") from exc
        for path in jit_paths:
            torch.jit.load(str(path), map_location="cpu")
            print(f"[LOAD-OK] {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
