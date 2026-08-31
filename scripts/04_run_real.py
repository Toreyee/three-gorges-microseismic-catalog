#!/usr/bin/env python3
"""Run REAL over daily pick directories with explicit, portable paths."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

REAL_OUTPUTS = ("catalog_sel.txt", "phase_sel.txt", "hypolocSA.dat", "hypophase.dat")


def date_value(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def append_text(source: Path, destination: Path) -> None:
    with source.open("r", encoding="utf-8", errors="replace") as reader, destination.open(
        "a", encoding="utf-8", newline="\n"
    ) as writer:
        for line in reader:
            writer.write(line.rstrip("\r\n") + "\n")


def append_renumbered_hypophase(source: Path, destination: Path, offset: int) -> int:
    maximum = offset
    with source.open("r", encoding="utf-8", errors="replace") as reader, destination.open(
        "a", encoding="utf-8", newline="\n"
    ) as writer:
        for line in reader:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                fields = stripped.split()
                if len(fields) < 15:
                    raise ValueError(f"unexpected REAL hypophase header: {stripped}")
                event_id = int(fields[14]) + offset
                fields[14] = str(event_id)
                maximum = max(maximum, event_id)
                writer.write(" ".join(fields) + "\n")
            else:
                writer.write(stripped + "\n")
    return maximum


def convert_phase_sel(source: Path, destination: Path) -> None:
    event_number = 0
    with source.open("r", encoding="utf-8", errors="replace") as reader, destination.open(
        "w", encoding="utf-8", newline="\n"
    ) as writer:
        for line_number, line in enumerate(reader, start=1):
            fields = line.split()
            if not fields:
                continue
            if fields[0].isdigit():
                if len(fields) < 17:
                    raise ValueError(f"{source}:{line_number}: short REAL event line")
                _, year, month, day, clock, _, _, lat, lon, depth, magnitude, *_ = fields
                hour, minute, second = clock.split(":")
                event_number += 1
                writer.write(
                    f"# {year} {month} {day} {hour} {minute} {second} {lat} {lon} "
                    f"{depth} {magnitude} 0.0 0.0 0.0 {event_number}\n"
                )
            else:
                if len(fields) < 8:
                    raise ValueError(f"{source}:{line_number}: short REAL phase line")
                _, station, phase, _, pick, _, _, probability, *_ = fields
                writer.write(f"{station} {pick} {probability} {phase}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", type=Path, required=True, help="REAL executable")
    parser.add_argument("--picks-root", type=Path, required=True, help="daily YYYYMMDD pick directories")
    parser.add_argument("--station", type=Path, required=True)
    parser.add_argument("--travel-time-table", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start-date", type=date_value, default=date(2018, 1, 1))
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--latitude-center", type=float, default=31.0)
    parser.add_argument("--R", default="0.3/20/0.02/1/5")
    parser.add_argument("--G", default="1.4/30/0.01/1")
    parser.add_argument("--V", default="6.0/3.3/4.8/2.8")
    parser.add_argument("--S", default="8/5/13/5/0.5/0.1/1/0.25/0.2/4")
    parser.add_argument("--skip-missing-days", action="store_true")
    args = parser.parse_args()

    for path in (args.real, args.station, args.travel_time_table):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not args.picks_root.is_dir():
        raise NotADirectoryError(args.picks_root)
    if args.days <= 0:
        parser.error("--days must be positive")

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    phase_sa = output / "phaseSA_allday.txt"
    phase_raw = output / "phase_allday.raw.txt"
    catalog_all = output / "catalog_allday.txt"
    for aggregate in (phase_sa, phase_raw, catalog_all):
        if aggregate.exists():
            raise FileExistsError(f"refusing to append to existing output: {aggregate}")

    event_offset = 0
    processed = 0
    for index in range(args.days):
        current = args.start_date + timedelta(days=index)
        day_code = current.strftime("%Y%m%d")
        picks = args.picks_root / day_code
        if not picks.is_dir():
            if args.skip_missing_days:
                print(f"[skip] missing {picks}")
                continue
            raise NotADirectoryError(picks)

        day_output = output / "daily" / day_code
        if day_output.exists():
            raise FileExistsError(f"refusing to overwrite daily output: {day_output}")
        day_output.mkdir(parents=True)
        day_argument = current.strftime(f"%Y/%m/%d/{args.latitude_center:g}")
        command = [
            str(args.real.resolve()), f"-D{day_argument}", f"-R{args.R}", f"-S{args.S}",
            f"-G{args.G}", f"-V{args.V}", str(args.station.resolve()), str(picks.resolve()),
            str(args.travel_time_table.resolve()),
        ]
        print("+", " ".join(command))
        subprocess.run(command, cwd=day_output, check=True)
        for name in REAL_OUTPUTS:
            generated = day_output / name
            if not generated.is_file():
                raise FileNotFoundError(f"REAL did not create {generated}")
            renamed = day_output / f"{day_code}.{name}"
            generated.rename(renamed)

        append_text(day_output / f"{day_code}.catalog_sel.txt", catalog_all)
        append_text(day_output / f"{day_code}.phase_sel.txt", phase_raw)
        event_offset = append_renumbered_hypophase(
            day_output / f"{day_code}.hypophase.dat", phase_sa, event_offset
        )
        processed += 1

    phase_all = output / "phase_allday.txt"
    convert_phase_sel(phase_raw, phase_all)
    print(f"processed {processed} days; final event id={event_offset}; output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
