#!/usr/bin/env python3
"""Integrate four hypoDD catalogs with explicit, auditable parameters."""

from __future__ import annotations

import argparse
from pathlib import Path

from tgr_catalog.catalog import integrate_model_catalogs, write_integration_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eqt", type=Path, required=True, help="EQTransformer hypoDD.reloc")
    parser.add_argument("--rnn", type=Path, required=True, help="RNN hypoDD.reloc")
    parser.add_argument("--unet", type=Path, required=True, help="Unet hypoDD.reloc")
    parser.add_argument("--lppnl", type=Path, required=True, help="LPPNL hypoDD.reloc")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--time-threshold", type=float, default=2.0, help="Single-link threshold in seconds")
    parser.add_argument("--quality-column", default="rms_ct_s")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    groups = integrate_model_catalogs(
        {"EQT": args.eqt, "RNN": args.rnn, "Unet": args.unet, "lppnl": args.lppnl},
        kind="reloc",
        threshold_seconds=args.time_threshold,
        quality_column=args.quality_column,
        select="min",
    )
    write_integration_result(groups, args.output_dir)
    print(f"Wrote {sum(map(len, groups.values())):,} events to {args.output_dir}")


if __name__ == "__main__":
    main()

