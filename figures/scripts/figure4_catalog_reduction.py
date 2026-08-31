import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# =========================
# 1. Data
# =========================
models = ["EQT", "RNN", "Unet", "LPPNL"]

# Event counts
real_counts = np.array([8392, 7863, 7078, 6733])
velest_counts = np.array([7913, 7538, 6748, 6460])
hypodd_counts = np.array([4517, 4298, 3907, 3912])

# Mean travel-time residuals
# VELEST values converted from seconds to milliseconds
velest_rms_ms = np.array([190.0, 170.0, 190.0, 180.0])
hypodd_rms_ms = np.array([34.295, 28.06, 21.624, 20.912])

# =========================
# 2. Style
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
    "savefig.facecolor": "white",
    "savefig.edgecolor": "white",
})

edge_c = "black"
fc_real = "white"
fc_velest = "0.75"
fc_hypodd = "0.40"

x = np.arange(len(models))

# =========================
# 3. Figure layout
# =========================
fig, axes = plt.subplots(
    1, 2,
    figsize=(8.2, 3.6),
    dpi=300,
    gridspec_kw={"width_ratios": [1.25, 1.0]}
)

plt.subplots_adjust(
    left=0.08, right=0.995,
    bottom=0.17, top=0.82,
    wspace=0.32
)

# =========================
# 4. Panel (a): Catalog reduction
# =========================
ax = axes[0]
w = 0.22

b1 = ax.bar(
    x - w, real_counts, width=w,
    color=fc_real, edgecolor=edge_c, linewidth=0.8, label="REAL"
)
b2 = ax.bar(
    x, velest_counts, width=w,
    color=fc_velest, edgecolor=edge_c, linewidth=0.8, label="VELEST"
)
b3 = ax.bar(
    x + w, hypodd_counts, width=w,
    color=fc_hypodd, edgecolor=edge_c, linewidth=0.8, label="hypoDD"
)

ax.set_title("(a) Catalog reduction", pad=6)
ax.set_ylabel("Number of events")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0, 9200)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# value labels
for bars, offset in zip([b1, b2, b3], [60, 60, 60]):
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2+0.05,
            h + offset,
            f"{int(h)}",
            ha="center", va="bottom", fontsize=7.5
        )

# =========================
# 5. Panel (b): Residual improvement
# =========================
ax = axes[1]
w2 = 0.28

r1 = ax.bar(
    x - w2/2, velest_rms_ms, width=w2,
    color=fc_velest, edgecolor=edge_c, linewidth=0.8, label="VELEST"
)
r2 = ax.bar(
    x + w2/2, hypodd_rms_ms, width=w2,
    color=fc_hypodd, edgecolor=edge_c, linewidth=0.8, label="hypoDD"
)

ax.set_title("(b) Residual improvement", pad=6)
ax.set_ylabel("Mean travel-time residual (ms)")
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0, 210)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# value labels
for bar in r1:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2,
        h + 4,
        f"{h:.0f}",
        ha="center", va="bottom", fontsize=7.5
    )

for bar in r2:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width()/2,
        h + 4,
        f"{h:.1f}",
        ha="center", va="bottom", fontsize=7.5
    )

# =========================
# 6. Global legend
# =========================
legend_handles = [
    Patch(facecolor=fc_real, edgecolor=edge_c, label="REAL"),
    Patch(facecolor=fc_velest, edgecolor=edge_c, label="VELEST"),
    Patch(facecolor=fc_hypodd, edgecolor=edge_c, label="hypoDD"),
]

fig.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.995),
    ncol=3,
    frameon=False,
    columnspacing=1.4,
    handletextpad=0.6
)

# =========================
# 7. Save
# =========================
outname = "Fig4_catalog_reduction_residual_improvement"

fig.savefig(f"{outname}.pdf", bbox_inches="tight")
fig.savefig(f"{outname}.svg", bbox_inches="tight")
fig.savefig(f"{outname}.png", dpi=600, bbox_inches="tight")

plt.show()
