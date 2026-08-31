import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# =========================
# Data
# =========================
models = ["EQT", "RNN", "Unet", "LPPNL"]

picked_before = np.array([596, 490, 638, 517])
recall_before = np.array([32.8, 27.1, 37.9, 30.1])
precision_before = np.array([72.0, 72.4, 77.7, 76.1])
f1_before = np.array([45.1, 39.5, 51.0, 43.1])

picked_after = np.array([853, 923, 874, 867])
recall_after = np.array([49.7, 54.1, 50.6, 49.8])
precision_after = np.array([79.2, 76.6, 75.7, 75.0])
f1_after = np.array([60.2, 63.4, 60.7, 59.9])

# =========================
# Style
# =========================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

before_fc = "white"
after_fc = "0.40"
edge_c = "black"

x = np.arange(len(models))

# 拉宽中间面板，避免拥挤
fig, axes = plt.subplots(
    1, 3, figsize=(10.8, 3.6), dpi=300,
    gridspec_kw={"width_ratios": [1.0, 1.35, 1.0]}
)

# 给顶部留空间放总图例
plt.subplots_adjust(left=0.07, right=0.995, bottom=0.16, top=0.82, wspace=0.35)

# -------------------------
# (a) Recall
# -------------------------
ax = axes[0]
w = 0.34
b1 = ax.bar(
    x - w/2, recall_before, width=w,
    color=before_fc, edgecolor=edge_c, linewidth=0.8
)
b2 = ax.bar(
    x + w/2, recall_after, width=w,
    color=after_fc, edgecolor=edge_c, linewidth=0.8
)

ax.set_title("(a) Recall", pad=6)
ax.set_ylabel("Recall (%)")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0, 62)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

#for bars in [b1, b2]:
#    for bar in bars:
#        h = bar.get_height()
#        ax.text(
#            bar.get_x() + bar.get_width()/2-0.1, h + 0.8, f"{h:.1f}",
#            ha="center", va="bottom", fontsize=8
#        )
for bar in b1:  # Before
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2-0.05, h + 0.8, f"{h:.1f}",
        ha="center", va="bottom", fontsize=8,
        
    )

for bar in b2:  # After
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2, h + 0.8, f"{h:.1f}",
        ha="center", va="bottom", fontsize=8
    )
# -------------------------
# (b) Precision and F1
# -------------------------
ax = axes[1]
w2 = 0.18

bp1 = ax.bar(
    x - 1.5*w2, precision_before, width=w2,
    color="white", edgecolor="black", linewidth=0.8, hatch="///"
)
bp2 = ax.bar(
    x - 0.5*w2, precision_after, width=w2,
    color="0.40", edgecolor="black", linewidth=0.8, hatch="///"
)
bf1 = ax.bar(
    x + 0.5*w2, f1_before, width=w2,
    color="white", edgecolor="black", linewidth=0.8
)
bf2 = ax.bar(
    x + 1.5*w2, f1_after, width=w2,
    color="0.40", edgecolor="black", linewidth=0.8
)

ax.set_title("(b) Precision and F1", pad=6)
ax.set_ylabel("Score (%)")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0, 88)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# 只标 after 数值，避免拥挤
for bars in [bp2, bf2]:
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2, h + 0.8, f"{h:.1f}",
            ha="center", va="bottom", fontsize=7.5
        )

# -------------------------
# (c) Picked phases
# -------------------------
ax = axes[2]
b3 = ax.bar(
    x - w/2, picked_before, width=w,
    color=before_fc, edgecolor=edge_c, linewidth=0.8
)
b4 = ax.bar(
    x + w/2, picked_after, width=w,
    color=after_fc, edgecolor=edge_c, linewidth=0.8
)

ax.set_title("(c) Picked phases", pad=6)
ax.set_ylabel("Number of picked phases")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0, 1020)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

#for bars in [b3, b4]:
#    for bar in bars:
#        h = bar.get_height()
#        ax.text(
#            bar.get_x() + bar.get_width()/2, h + 12, f"{int(h)}",
#            ha="center", va="bottom", fontsize=8
#        )
for bar in b3:  # Before
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2-0.05, h + 0.8, f"{int(h)}",
        ha="center", va="bottom", fontsize=8,
        
    )

for bar in b4:  # After
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2, h + 0.8, f"{int(h)}",
        ha="center", va="bottom", fontsize=8
    )
# =========================
# Global legend (outside)
# =========================
legend_handles = [
    Patch(facecolor="white", edgecolor="black", label="Before"),
    Patch(facecolor="0.40", edgecolor="black", label="After"),
    Patch(facecolor="white", edgecolor="black", hatch="///", label="Precision"),
    Patch(facecolor="white", edgecolor="black", label="F1"),
]

fig.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.98),
    ncol=4,
    frameon=False,
    columnspacing=1.4,
    handletextpad=0.6
)

# =========================
# Save
# =========================
outname = "Fig3_transfer_learning_performance_JAG_v2"
fig.savefig(f"{outname}.pdf", bbox_inches="tight")
fig.savefig(f"{outname}.svg", bbox_inches="tight")
fig.savefig(f"{outname}.png", dpi=600, bbox_inches="tight")
plt.show()