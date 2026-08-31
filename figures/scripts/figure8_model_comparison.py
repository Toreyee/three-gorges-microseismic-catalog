#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
plot_model_comparison_final_gray.py

Final grayscale, publication-oriented model-comparison figure.

Input
-----
--summary-csv : summary table with columns:
                model, mc_paper_style, mc_strict_maxc, n_events_strict

Output
------
<out-prefix>.png
<out-prefix>.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def normalize_model_name(name: str) -> str:
    """Normalize model names for ordering while preserving publication display."""
    s = str(name).strip()
    low = s.lower()
    if low in {"eqt", "eqtransformer", "eqtransformer"}:
        return "EQT"
    if low == "rnn":
        return "RNN"
    if low in {"unet", "u-net"}:
        return "Unet"
    if low == "lppnl":
        return "LPPNL"
    return s


def load_summary(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"model", "mc_paper_style", "mc_strict_maxc", "n_events_strict"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"summary 缺少必要列: {sorted(missing)}")

    df = df.copy()
    df["model_display"] = df["model"].map(normalize_model_name)

    order = ["EQT", "RNN", "Unet", "LPPNL"]
    order_map = {m: i for i, m in enumerate(order)}
    df["order"] = df["model_display"].map(order_map)

    if df["order"].isna().any():
        unknown = df.loc[df["order"].isna(), "model"].tolist()
        raise ValueError(f"无法识别模型名称，请检查 model 列: {unknown}")

    df = df.sort_values("order").drop(columns="order").reset_index(drop=True)
    return df


def style_axes(ax):
    ax.grid(True, axis="y", color="0.90", linewidth=0.42)
    ax.grid(False, axis="x")

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.90)

    ax.tick_params(axis="both", which="major", direction="in", width=0.90, length=4.2)
    ax.tick_params(axis="both", which="minor", direction="in", width=0.70, length=2.4)


def add_labels(ax, x, y, fmt="float", frac=0.012, fontsize=6.7):
    ymin, ymax = ax.get_ylim()
    yr = ymax - ymin
    for xi, yi in zip(x, y):
        txt = f"{int(yi)}" if fmt == "int" else f"{yi:.2f}"
        ax.text(
            xi,
            yi + yr * frac,
            txt,
            ha="center",
            va="bottom",
            fontsize=fontsize,
            color="0.05",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Draw final grayscale model-comparison figure."
    )
    parser.add_argument("--summary-csv", default="fig7_model_comparison.summary.csv")
    parser.add_argument("--out-prefix", default="fig_model_comparison_final_gray")
    parser.add_argument("--dpi", type=int, default=900)
    args = parser.parse_args()

    df = load_summary(args.summary_csv)

    models = df["model_display"].tolist()
    x = np.arange(len(models))

    # ---------------- Publication-style typography ----------------
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Serif",
        "mathtext.fontset": "dejavuserif",
        "font.size": 7.2,
        "axes.labelsize": 8.3,
        "axes.titlesize": 8.1,
        "xtick.labelsize": 7.9,
        "ytick.labelsize": 7.9,
        "axes.linewidth": 0.9,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.minor.width": 0.7,
        "ytick.minor.width": 0.7,
        "legend.frameon": False,
    })

    # ---------------- Grayscale palette ----------------
    bar_gray_a = "0.82"   # panels a and b
    bar_gray_c = "0.78"   # panel c, slightly darker but still grayscale
    line_gray = "0.18"
    marker_gray = "0.18"

    fig, axes = plt.subplots(1, 3, figsize=(7.15, 2.62))

    # ---------------- (a) Cumulative-fit Mc ----------------
    ax = axes[0]
    y = df["mc_paper_style"].to_numpy(dtype=float)

    ax.bar(
        x, y,
        width=0.60,
        color=bar_gray_a,
        edgecolor="none",
        linewidth=0,
        zorder=1,
    )
    ax.plot(
        x, y,
        color=line_gray,
        marker="o",
        linewidth=1.10,
        markersize=3.1,
        markerfacecolor=marker_gray,
        markeredgecolor=marker_gray,
        zorder=2,
    )

    ax.set_xticks(x, models)
    ax.set_ylim(0.0, 0.78)
    ax.set_ylabel(r"$M_c$")
    ax.set_title(r"(a) Cumulative-fit $M_c$", pad=6, loc="left")
    style_axes(ax)
    add_labels(ax, x, y, fmt="float", frac=0.014, fontsize=6.8)

    # ---------------- (b) MAXC Mc ----------------
    ax = axes[1]
    y = df["mc_strict_maxc"].to_numpy(dtype=float)

    ax.bar(
        x, y,
        width=0.60,
        color=bar_gray_a,
        edgecolor="none",
        linewidth=0,
        zorder=1,
    )
    ax.plot(
        x, y,
        color=line_gray,
        marker="o",
        linewidth=1.10,
        markersize=3.1,
        markerfacecolor=marker_gray,
        markeredgecolor=marker_gray,
        zorder=2,
    )

    ax.set_xticks(x, models)
    ax.set_ylim(0.0, 0.84)
    ax.set_ylabel(r"$M_c$")
    ax.set_title(r"(b) MAXC $M_c$", pad=6, loc="left")
    style_axes(ax)
    add_labels(ax, x, y, fmt="float", frac=0.010, fontsize=6.8)

    # ---------------- (c) Effective event count ----------------
    ax = axes[2]
    y = df["n_events_strict"].to_numpy(dtype=float)

    ax.bar(
        x, y,
        width=0.60,
        color=bar_gray_c,
        edgecolor="none",
        linewidth=0,
        zorder=1,
    )
    ax.plot(
        x, y,
        color=line_gray,
        marker="o",
        linewidth=1.10,
        markersize=3.1,
        markerfacecolor=marker_gray,
        markeredgecolor=marker_gray,
        zorder=2,
    )

    ax.set_xticks(x, models)
    ax.set_ylim(0.0, 3420)
    ax.set_ylabel("Effective event count")
    ax.set_title("(c) Effective event counts", pad=6, loc="left")
    style_axes(ax)
    add_labels(ax, x, y, fmt="int", frac=0.010, fontsize=6.6)

    fig.subplots_adjust(left=0.072, right=0.992, bottom=0.22, top=0.86, wspace=0.28)

    out_png = Path(f"{args.out_prefix}.png")
    out_pdf = Path(f"{args.out_prefix}.pdf")

    fig.savefig(out_png, dpi=args.dpi, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")

    print(f"写出: {out_png}")
    print(f"写出: {out_pdf}")


if __name__ == "__main__":
    main()
