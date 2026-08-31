#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
plot_eqt_fmd_publication_final_gray.py

Final grayscale, publication-oriented FMD figure for the recalibrated EQTransformer catalog.

Inputs
------
--event-csv   : event catalog with column "ml_event"
--summary-csv : paper-style Mc fitting summary with columns:
                mc_paper_style, r2, slope_log10cum, intercept_log10cum, bin_width

Outputs
-------
<out-prefix>.png
<out-prefix>.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, LogLocator, NullFormatter


def build_fmd(mags: np.ndarray, bin_width: float):
    """Build non-cumulative and cumulative magnitude-frequency distributions."""
    mmin = np.floor(mags.min() / bin_width) * bin_width
    mmax = np.ceil(mags.max() / bin_width) * bin_width + bin_width
    bins = np.arange(mmin, mmax + bin_width, bin_width)
    hist, edges = np.histogram(mags, bins=bins)
    centers = edges[:-1] + bin_width / 2.0
    cum = np.cumsum(hist[::-1])[::-1]
    return centers, hist, cum, bins


def main():
    parser = argparse.ArgumentParser(
        description="Draw final grayscale FMD figure for the recalibrated EQTransformer catalog."
    )
    parser.add_argument("--event-csv", default="manual_recalib_eval.strict.csv")
    parser.add_argument("--summary-csv", default="paper_style_mc_strict.summary.csv")
    parser.add_argument("--out-prefix", default="fig7_eqt_fmd_final_gray")
    parser.add_argument("--bin-width", type=float, default=None)
    parser.add_argument("--dpi", type=int, default=900)
    args = parser.parse_args()

    event_path = Path(args.event_csv)
    summary_path = Path(args.summary_csv)

    if not event_path.exists():
        raise FileNotFoundError(f"Event CSV not found: {event_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary CSV not found: {summary_path}")

    evt = pd.read_csv(event_path)
    if "ml_event" not in evt.columns:
        raise ValueError('Event CSV must contain column "ml_event".')

    mags = pd.to_numeric(evt["ml_event"], errors="coerce").dropna().to_numpy(dtype=float)
    if len(mags) == 0:
        raise RuntimeError("No valid ml_event values found.")

    summ = pd.read_csv(summary_path)
    if len(summ) == 0:
        raise RuntimeError("Summary CSV is empty.")

    required = ["mc_paper_style", "r2", "slope_log10cum", "intercept_log10cum", "bin_width"]
    missing = [c for c in required if c not in summ.columns]
    if missing:
        raise ValueError(f"Summary CSV missing required columns: {missing}")

    row = summ.iloc[0]
    mc = float(row["mc_paper_style"])
    r2 = float(row["r2"])
    slope = float(row["slope_log10cum"])
    intercept = float(row["intercept_log10cum"])
    bin_width = float(args.bin_width if args.bin_width is not None else row["bin_width"])

    centers, hist, cum, _ = build_fmd(mags, bin_width=bin_width)

    fit_mask = centers >= mc
    fit_x = centers[fit_mask]
    fit_y = 10 ** (slope * fit_x + intercept)

    # ---------------- Publication-style typography ----------------
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Serif",
        "mathtext.fontset": "dejavuserif",
        "font.size": 8.0,
        "axes.labelsize": 9.6,
        "axes.titlesize": 9.4,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,
        "axes.linewidth": 0.9,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.minor.width": 0.7,
        "ytick.minor.width": 0.7,
        "xtick.major.size": 4.6,
        "ytick.major.size": 4.6,
        "xtick.minor.size": 2.6,
        "ytick.minor.size": 2.6,
    })

    # ---------------- Grayscale palette ----------------
    bar_gray = "0.84"      # light gray fill
    line_gray = "0.22"     # dark gray data curves
    mc_gray = "0.10"       # near-black Mc line
    fit_gray = "0.00"      # black GR fit
    grid_gray = "0.91"     # very light major grid

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.15, 2.82))

    xmin = min(-1.6, centers.min() - 0.1)
    xmax = max(3.1, centers.max() + 0.1)

    # ---------------- (a) Non-cumulative FMD ----------------
    ax1.bar(
        centers, hist,
        width=bin_width * 0.92,
        color=bar_gray,
        edgecolor="none",
        linewidth=0,
        zorder=1,
    )

    ax1.plot(
        centers, hist,
        color=line_gray,
        marker="o",
        markersize=3.25,
        linewidth=1.25,
        markerfacecolor=line_gray,
        markeredgecolor=line_gray,
        zorder=3,
    )

    ax1.axvline(
        mc,
        color=mc_gray,
        linestyle=(0, (4.5, 2.5)),
        linewidth=1.10,
        zorder=2,
    )

    ax1.set_yscale("log")
    ax1.set_xlim(xmin, xmax)
    ax1.set_xlabel(r"Local magnitude, $M_L$")
    ax1.set_ylabel("Frequency")
    ax1.set_title("Non-cumulative FMD", pad=5)

    ax1.text(
        0.03, 0.95, "(a)",
        transform=ax1.transAxes,
        ha="left",
        va="top",
        fontsize=9.4,
        fontweight="bold",
    )

    ax1.text(
        0.97, 0.95,
        fr"$M_c$ = {mc:.2f}",
        transform=ax1.transAxes,
        ha="right",
        va="top",
        fontsize=8.6,
    )

    # ---------------- (b) Cumulative FMD and GR fit ----------------
    ax2.plot(
        centers, cum,
        color=line_gray,
        marker="o",
        markersize=3.25,
        linewidth=1.25,
        markerfacecolor=line_gray,
        markeredgecolor=line_gray,
        zorder=3,
    )

    ax2.plot(
        fit_x, fit_y,
        color=fit_gray,
        linewidth=1.25,
        linestyle="-",
        zorder=4,
    )

    ax2.axvline(
        mc,
        color=mc_gray,
        linestyle=(0, (4.5, 2.5)),
        linewidth=1.10,
        zorder=2,
    )

    ax2.set_yscale("log")
    ax2.set_xlim(xmin, xmax)
    ax2.set_xlabel(r"Local magnitude, $M_L$")
    ax2.set_ylabel("Cumulative number")
    ax2.set_title("Cumulative FMD and GR fit", pad=5)

    ax2.text(
        0.03, 0.95, "(b)",
        transform=ax2.transAxes,
        ha="left",
        va="top",
        fontsize=9.4,
        fontweight="bold",
    )

    ax2.text(
        0.97, 0.95,
        fr"$M_c$ = {mc:.2f}" + "\n" + fr"$R^2$ = {r2:.3f}",
        transform=ax2.transAxes,
        ha="right",
        va="top",
        fontsize=8.6,
    )

    # ---------------- Shared axis formatting ----------------
    for ax in (ax1, ax2):
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1))
        ax.yaxis.set_minor_formatter(NullFormatter())

        ax.grid(True, which="major", color=grid_gray, linewidth=0.42)
        ax.grid(False, which="minor")

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.9)

    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.20, top=0.875, wspace=0.19)

    out_png = Path(f"{args.out_prefix}.png")
    out_pdf = Path(f"{args.out_prefix}.pdf")

    fig.savefig(out_png, dpi=args.dpi, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")

    print(f"写出: {out_png}")
    print(f"写出: {out_pdf}")


if __name__ == "__main__":
    main()
