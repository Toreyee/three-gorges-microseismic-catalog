#!/usr/bin/env python3
"""Convert comma-separated phase picks to REAL daily station-phase files."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_time(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported pick timestamp: {value!r}")


def station_name(raw: str, network: str) -> str:
    parts = raw.strip().split(".")
    station = parts[1] if len(parts) >= 2 else parts[0]
    if not station:
        raise ValueError(f"empty station name in {raw!r}")
    return f"{network}.{station}" if network else station


def convert(input_path: Path, output_dir: Path, network: str) -> Counter:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if output_dir.exists() and any(output_dir.glob("????????/*.txt")):
        raise FileExistsError(
            f"refusing to append to existing REAL phase files: {output_dir}; use a fresh output directory"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: Counter = Counter()
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, row in enumerate(csv.reader(handle), start=1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            row = [value.strip() for value in row if value.strip()]
            if len(row) < 5:
                raise ValueError(f"{input_path}:{line_number}: expected at least 5 CSV fields")
            phase = row[0].upper()
            if phase not in {"P", "S"}:
                raise ValueError(f"{input_path}:{line_number}: unsupported phase {phase!r}")
            offset_seconds = float(row[1])
            probability = float(row[2])
            station = station_name(row[3], network)
            origin = parse_time(row[4])
            day_dir = output_dir / origin.strftime("%Y%m%d")
            day_dir.mkdir(parents=True, exist_ok=True)
            destination = day_dir / f"{station}.{phase}.txt"
            with destination.open("a", encoding="utf-8", newline="\n") as writer:
                writer.write(f"{offset_seconds:g} {probability:g} 0\n")
            counts[phase] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", type=Path, required=True, help="picker CSV text file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="REAL input root")
    parser.add_argument("--network", default="SX", help="output network code")
    args = parser.parse_args()
    counts = convert(args.input, args.output, args.network)
    print(f"wrote P={counts['P']} S={counts['S']} picks to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
