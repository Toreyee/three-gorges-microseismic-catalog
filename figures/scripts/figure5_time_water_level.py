import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

# =========================
# 1. Read water level file
# =========================
water = pd.read_csv(
    "water.lev",
    sep=r"\s+",
    header=None,
    names=["year", "month", "day", "hour", "level"]
)

water = water[water["year"] == 2018].copy()
water["datetime"] = pd.to_datetime(
    dict(year=water.year, month=water.month, day=water.day, hour=water.hour)
)
water["date"] = water["datetime"].dt.floor("D")

water_daily = (
    water.groupby("date", as_index=False)["level"]
    .mean()
    .rename(columns={"level": "water_level"})
)

# =========================
# 2. Read manual catalog
# =========================
manual = pd.read_csv(
    "2018.cat.txt",
    sep=r"\s+",
    header=None,
    usecols=[0],
    names=["date"]
)
manual["date"] = pd.to_datetime(manual["date"].astype(str), format="%Y%m%d")
manual_daily = manual.groupby("date").size().reset_index(name="manual_count")

# =========================
# 3. Read final catalog
# =========================
final = pd.read_csv(
    "ALL.txt",
    sep=r"\s+",
    header=None,
    usecols=[10, 11, 12, 13, 14, 15],
    names=["year", "month", "day", "hour", "minute", "second"]
)

final["datetime"] = (
    pd.to_datetime(
        dict(
            year=final["year"],
            month=final["month"],
            day=final["day"],
            hour=final["hour"],
            minute=final["minute"]
        )
    )
    + pd.to_timedelta(final["second"], unit="s")
)
final["date"] = final["datetime"].dt.floor("D")
final_daily = final.groupby("date").size().reset_index(name="final_count")

# =========================
# 4. Merge to full 2018 date range
# =========================
date_range = pd.DataFrame({
    "date": pd.date_range("2018-01-01", "2018-12-31", freq="D")
})

df = date_range.merge(water_daily, on="date", how="left")
df = df.merge(manual_daily, on="date", how="left")
df = df.merge(final_daily, on="date", how="left")

df["manual_count"] = df["manual_count"].fillna(0)
df["final_count"] = df["final_count"].fillna(0)

df["manual_ma7"] = df["manual_count"].rolling(7, center=True, min_periods=1).mean()
df["final_ma7"] = df["final_count"].rolling(7, center=True, min_periods=1).mean()
df["water_ma7"] = df["water_level"].rolling(7, center=True, min_periods=1).mean()

# =========================
# 5. Plot style
# =========================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

# =========================
# Publication-oriented colors
# =========================
COLOR_WATER = "#4F7FA8"   # muted blue-gray
COLOR_MANUAL = "#666666"  # medium-dark gray
COLOR_FINAL = "#8C2D2D"   # muted dark red

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(8.2, 4.3),
    dpi=300,
    sharex=True,
    gridspec_kw={"height_ratios": [0.9, 1.25]}
)
fig.subplots_adjust(hspace=0.14)

# =========================
# 6. Panel (a): Water level
# =========================
ax1.plot(df["date"], df["water_ma7"], lw=1.8, color=COLOR_WATER)
ax1.set_ylabel("Water level (m)")
ax1.text(
    0.01, 0.92, "(a) Reservoir water level",
    transform=ax1.transAxes, ha="left", va="top",
    fontsize=9, fontweight="bold"
)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# =========================
# 7. Panel (b): Event counts
# =========================
ax2.plot(df["date"], df["manual_ma7"], lw=1.7, color=COLOR_MANUAL)
ax2.plot(df["date"], df["final_ma7"], lw=2.1, color=COLOR_FINAL)

ax2.set_ylabel("Events per day")
ax2.set_ylim(0, 90)
ax2.set_yticks([0, 20, 40, 60, 80])

ax2.text(
    0.01, 0.92, "(b) Event counts",
    transform=ax2.transAxes, ha="left", va="top",
    fontsize=9, fontweight="bold"
)

ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

legend_handles = [
    Line2D([0], [0], color=COLOR_MANUAL, lw=1.7, label="Official catalog"),
    Line2D([0], [0], color=COLOR_FINAL, lw=2.1, label="Final catalog")
]

ax2.legend(
    handles=legend_handles,
    frameon=False,
    loc="upper right",
    bbox_to_anchor=(0.98, 0.98),
    ncol=1,
    borderaxespad=0.2,
    handlelength=2.2
)

# =========================
# 8. Shared x axis formatting
# =========================
ax2.set_xlabel("Date in 2018")
ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax2.set_xlim(pd.Timestamp("2018-01-01"), pd.Timestamp("2018-12-31"))

fig.savefig("Fig5_time_distribution_water_level_final2.pdf", bbox_inches="tight")
fig.savefig("Fig5_time_distribution_water_level_final2.png", dpi=600, bbox_inches="tight")
plt.show()