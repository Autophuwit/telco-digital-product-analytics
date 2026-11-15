"""Render the portfolio charts.

All figures are RESCALED / INDEXED versions of the original results: counts are scaled,
rates are slightly perturbed and money is shown as an index. Relative patterns are preserved.
Usage: python make_charts.py <output_dir>
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"
GRAY = "#b9b8b0"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.grid": False,
    "axes.spines.top": False, "axes.spines.right": False,
})

def title(ax, t, sub):
    ax.set_title(t, loc="left", fontsize=14, fontweight="bold", color=INK, pad=28)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10, color=INK2, va="bottom")

def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=200)
    plt.close(fig)

def grid_y(ax):
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)

# ---------------------------------------------------------------- 00 one-page report (Part 1)
from matplotlib.patches import FancyBboxPatch

PAGE, CARD, LINE = "#f4f3ef", "#ffffff", "#e1e0d9"
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
mau_po = [1.34, 1.28, 1.30, 1.06, 1.41, 1.40, 1.51, 1.49, 1.53, 1.54, 1.50, 1.43, 1.50]
mau_pp = [3.51, 3.28, 3.62, 3.68, 3.70, 3.78, 4.13, 3.96, 4.03, 3.98, 4.05, 4.18, 4.33]
dig_pct = [.105, .100, .109, .106, .115, .118, .128, .126, .121, .118, .127, .119, .133]
drv = {"DCB": [.061, .060, .061, .040, .066, .061, .065, .061, .065, .066, .064, .061, .065],
       "CPA": [.058, .054, .055, .053, .051, .052, .055, .056, .054, .054, .053, .050, .052],
       "OTT": [.0065, .0065, .0065, .0093, .0121, .0149, .0167, .0186, .0195, .0214, .0214, .0223, .0233],
       "Up2U": [.0037, .0037, .0047, .0047, .0056, .0056, .0065, .0065, .0065, .0056, .0047, .0047, .0037]}
M12 = [f"M{i}" for i in range(1, 13)]
surv = {"po_dig": [1, .981, .918, .898, .880, .859, .850, .830, .844, .800, .784, .663],
        "po_non": [1, .986, .927, .909, .889, .871, .853, .834, .813, .797, .776, .653],
        "pp_dig": [1, .955, .882, .853, .828, .796, .776, .751, .720, .690, .664, .489],
        "pp_non": [1, .905, .819, .791, .754, .723, .692, .664, .637, .610, .583, .482]}
gap_po = {"CPA": .02, "DCB": .00, "Up2U": -.05, "Game": -.16, "Security": -.11, "OTT": -.07}
gap_pp = {"CPA": .04, "DCB": .10, "Up2U": .05, "Game": .01, "Security": -.03, "OTT": -.09}

fig = plt.figure(figsize=(16, 10.2), facecolor=PAGE)

def card(x, y, w, h):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure, fc=CARD, ec=LINE, lw=1.1, zorder=-10))

def styled(ax):
    ax.set_facecolor(CARD)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(axis="both", labelsize=9, length=0, colors=MUTED)
    ax.grid(axis="y", color="#ecebe6", lw=0.8); ax.set_axisbelow(True)

# header
fig.text(0.03, 0.952, "Digital Product Performance", fontsize=25, fontweight="bold", color=INK)
fig.text(0.03, 0.918, "Monthly management report  ·  digital users vs non-digital users  ·  13-month view", fontsize=12, color=INK2)
fig.text(0.97, 0.952, "Portfolio recreation  ·  rescaled data", fontsize=10, color=MUTED, ha="right")

# KPI tiles
kpis = [("Digital product MAU", "5.8M", "+20% YoY", AQUA),
        ("Share of base using digital", "13%", "+3pp YoY", AQUA),
        ("ARPU uplift after adoption", "+10% | +29%", "Postpaid | Prepaid", AQUA),
        ("OTT 12-month survival vs non-digital", "-7pp | -9pp", "Postpaid | Prepaid", ORANGE)]
tw = (0.94 - 3 * 0.015) / 4
for i, (lab, val, sub, c) in enumerate(kpis):
    x = 0.03 + i * (tw + 0.015); y = 0.775; h = 0.115
    card(x, y, tw, h)
    fig.patches.append(plt.Rectangle((x, y + 0.012), 0.004, h - 0.024, transform=fig.transFigure, fc=c, ec="none", zorder=-5))
    fig.text(x + 0.018, y + h - 0.03, lab.upper(), fontsize=9, color=MUTED, fontweight="bold")
    fig.text(x + 0.018, y + 0.040, val, fontsize=24, fontweight="bold", color=ORANGE if c == ORANGE else INK)
    fig.text(x + 0.018, y + 0.014, sub, fontsize=10, color=INK2)

# panel grid
pw = (0.94 - 2 * 0.015) / 3; ph = 0.335
slots = [(0.03 + c * (pw + 0.015), 0.405 if r == 0 else 0.045) for r in range(2) for c in range(3)]

def panel(i, t, takeaway):
    x, y = slots[i]
    card(x, y, pw, ph)
    fig.text(x + 0.016, y + ph - 0.034, t, fontsize=13, fontweight="bold", color=INK)
    fig.text(x + 0.016, y + ph - 0.06, takeaway, fontsize=10, color=INK2)
    ax = fig.add_axes([x + 0.042, y + 0.045, pw - 0.06, ph - 0.125], zorder=5)
    styled(ax)
    return ax

ax = panel(0, "Digital product MAU", "Prepaid drives ~3/4 of digital users")
ax.bar(range(13), mau_po, color=VIOLET, width=0.68, label="Postpaid", zorder=2)
ax.bar(range(13), mau_pp, bottom=mau_po, color=AQUA, width=0.68, label="Prepaid", zorder=2)
for i in (0, 12):
    ax.text(i, mau_po[i] + mau_pp[i] + 0.15, f"{mau_po[i]+mau_pp[i]:.1f}M", ha="center", fontsize=9.5, color=INK, fontweight="bold")
ax.set_xticks(range(13), MON); ax.set_ylim(0, 7); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}M"))
ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=2, handlelength=1, borderaxespad=0)

ax = panel(1, "Postpaid adoption by product", "OTT is the fastest-growing product (x3.5)")
for (k, ys), c in zip(drv.items(), [YELLOW, VIOLET, ORANGE, MAGENTA]):
    lw = 2.8 if k == "OTT" else 1.8
    ax.plot(range(13), ys, color=c, lw=lw, marker="o", ms=3.5 if k != "OTT" else 5, zorder=3 if k == "OTT" else 2)
    ax.text(12.4, ys[-1], k, fontsize=9.5, color=c if k == "OTT" else INK2, va="center", fontweight="bold" if k == "OTT" else "normal")
ax.set_xticks(range(13), MON); ax.set_xlim(-0.4, 14.2); ax.set_ylim(0, 0.075)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))

ax = panel(2, "ARPU uplift by products added", "More digital products, bigger uplift")
cats = ["+1 product", "+2 products", "+3 products"]; po = [.08, .23, .52]; pp = [.29, .36, 1.14]
x = range(3); w = 0.36
b1 = ax.bar([i - w / 2 for i in x], po, w, color=VIOLET, label="Postpaid", zorder=2)
b2 = ax.bar([i + w / 2 for i in x], pp, w, color=AQUA, label="Prepaid", zorder=2)
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.03, f"+{b.get_height():.0%}", ha="center", fontsize=9, color=INK2)
ax.set_xticks(list(x), cats); ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0)); ax.set_ylim(0, 1.32)
ax.legend(frameon=False, fontsize=9, loc="upper left", handlelength=1, borderaxespad=0)

for idx, seg, take in [(3, "po", "Digital and non-digital retain about the same"), (4, "pp", "Digital users retain slightly better")]:
    ax = panel(idx, f"12-month survival · {'Postpaid' if seg == 'po' else 'Prepaid'}", take)
    d, n = surv[f"{seg}_dig"], surv[f"{seg}_non"]
    ax.fill_between(range(12), d, n, color=BLUE, alpha=0.08, lw=0)
    ax.plot(range(12), n, color=GRAY, lw=2, label="Non-digital")
    ax.plot(range(12), d, color=BLUE, lw=2.4, label="Digital")
    ax.text(11.25, d[-1] + 0.025, f"{d[-1]:.0%}", fontsize=9.5, color=BLUE, fontweight="bold")
    ax.text(11.25, n[-1] - 0.045, f"{n[-1]:.0%}", fontsize=9.5, color=INK2)
    ax.set_xticks(range(12), M12); ax.set_xlim(-0.3, 12.2); ax.set_ylim(0.4, 1.04)
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.legend(frameon=False, fontsize=9, loc="lower left", handlelength=1.5, borderaxespad=0)

ax = panel(5, "Survival gap vs non-digital, by product", "OTT is the only product negative in both segments")
prods = ["CPA", "DCB", "Up2U", "Game", "Security", "OTT"]; ys = list(range(len(prods)))[::-1]; h = 0.36
ax.axhspan(-0.5, 0.5, color="#fdebe3", zorder=0)
ax.barh([i + h / 2 for i in ys], [gap_po[p] for p in prods], h, color=VIOLET, label="Postpaid", zorder=2)
ax.barh([i - h / 2 for i in ys], [gap_pp[p] for p in prods], h, color=AQUA, label="Prepaid", zorder=2)
ax.axvline(0, color=AXIS, lw=1)
ax.set_yticks(ys, prods); ax.get_yticklabels()[-1].set_color(ORANGE); ax.get_yticklabels()[-1].set_fontweight("bold")
ax.grid(axis="y", visible=False); ax.grid(axis="x", color="#ecebe6", lw=0.8)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v*100:+.0f}pp" if v else "0"))
ax.set_xlim(-0.19, 0.13); ax.set_ylim(-0.6, 5.6)
ax.legend(frameon=False, fontsize=9, loc="upper left", handlelength=1, borderaxespad=0)

fig.savefig(os.path.join(OUT, "00_digital_product_report.png"), dpi=160, facecolor=PAGE)
plt.close(fig)

# ---------------------------------------------------------------- Part 2 charts
def hbar(name, t, sub, rows, ref=None, ref_label=None, xlim=(0.4, 1.0), highlight=()):
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(9, 0.48 * len(rows) + 1.6))
    labels = [r[0] for r in rows]; vals = [r[1] for r in rows]
    colors = [ORANGE if r[0] in highlight else BLUE for r in rows]
    ax.barh(labels, [v - xlim[0] for v in vals], left=xlim[0], height=0.62, color=colors, edgecolor=SURF, linewidth=2, zorder=2)
    for i, (lab, v, *n) in enumerate(rows):
        txt = f"{v:.1%}" + (f"   n={n[0]}" if n else "")
        if ref is not None and v > ref - 0.12:
            ax.text(v - 0.006, i, txt, va="center", ha="right", fontsize=10, color="#ffffff")
        else:
            ax.text(v + 0.005, i, txt, va="center", fontsize=10, color=INK2)
    if ref is not None:
        ax.axvline(ref, color=INK, lw=1.2, ls=(0, (3, 3)), zorder=0.5)
        ax.text(ref, len(rows) - 0.45, f" {ref_label} {ref:.1%}", fontsize=9.5, color=INK, va="bottom", ha="center",
                bbox=dict(facecolor=SURF, edgecolor="none", pad=1))
        ax.set_ylim(-0.6, len(rows) - 0.05)
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.set_xlabel("6-month survival rate (active caller M06 / M01)")
    title(ax, t, sub)
    save(fig, name)

ND = 0.905
hbar("01_survival_by_acquisition_path.png", "Gross Add is the leakiest way into OTT",
     "First-OTT cohort (Postpaid, n~143K) - M06 survival by how the customer got OTT",
     [("Change Main", .920, "16.5K"), ("Topping", .864, "97.2K"), ("Other", .803, "2.4K"), ("Gross Add", .721, "26.6K")],
     ref=ND, ref_label="Non-digital", xlim=(0.6, 1.0), highlight=("Gross Add",))
hbar("02_gross_add_by_switch_type.png", "Inside Gross Add, Pre2Post migrations churn the most",
     "First-OTT cohort, Gross Add only - M06 survival by switch-on type",
     [("MNP", .810, "1.1K"), ("New", .742, "18.4K"), ("Pre2Post", .653, "7.1K")],
     ref=ND, ref_label="Non-digital", xlim=(0.5, 1.0), highlight=("Pre2Post",))
hbar("03_pre2post_by_channel.png", "Same product, different seller: ~30pp gap between channels",
     "Pre2Post + OTT - M06 survival by sales channel",
     [("Dealer A", .849, "1.4K"), ("Dealer B", .678, "2.2K"), ("Other shops", .584, "590"),
      ("Contact Center", .554, "2.5K"), ("Own digital", .530, "250"), ("Modern trade", .385, "100")],
     ref=ND, ref_label="Non-digital", xlim=(0.3, 1.0), highlight=("Contact Center",))

m = [f"M{i}" for i in range(1, 10)]
fig, ax = plt.subplots(figsize=(9, 5))
for lab, ys, c, mk in [("Pre2Post (no OTT)", [1, .986, .975, .846, .760, .709, .672, .649, .628], GRAY, "o"),
                       ("Pre2Post + OTT, prepaid tenure > 5Y", [1, .985, .970, .905, .834, .781, .723, .740, .716], BLUE, "s"),
                       ("Pre2Post + OTT, prepaid tenure <= 5Y", [1, .985, .970, .829, .711, .640, .562, .536, .459], ORANGE, "D")]:
    ax.plot(m, ys, color=c, lw=2, marker=mk, ms=6, markeredgecolor=SURF, markeredgewidth=1.5, label=lab)
    ax.text(8.15, ys[-1], f"{ys[-1]:.0%}", va="center", fontsize=10, color=INK2)
ax.set_ylim(0.4, 1.02); ax.set_xlim(-0.3, 8.6)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0)); grid_y(ax)
ax.legend(frameon=False, loc="lower left", fontsize=10); ax.set_ylabel("Survival rate (cohort-weighted)")
title(ax, "Short-tenure Pre2Post customers fall off a cliff after month 3",
      "Pre2Post gross adds - survival curve split by tenure on the prior prepaid SIM")
save(fig, "04_pre2post_tenure_curve.png")

bands = ["<=0%", "0-50%", "50-100%", "100-200%", "200-300%", ">300%"]
top = [.897, .899, .875, .870, .869, .853]; both = [.883, .884, .833, .820, .813, .738]
fig, ax = plt.subplots(figsize=(9, 5)); x = range(len(bands))
ax.plot(x, top, color=BLUE, lw=2, marker="o", ms=7, markeredgecolor=SURF, markeredgewidth=1.5, label="Topping only")
ax.plot(x, both, color=ORANGE, lw=2, marker="D", ms=7, markeredgecolor=SURF, markeredgewidth=1.5, label="Topping + Change Main, same month")
ax.text(5.12, top[-1], f"{top[-1]:.0%}", va="center", fontsize=10, color=INK2)
ax.text(5.12, both[-1], f"{both[-1]:.0%}", va="center", fontsize=10, color=INK2)
ax.axhline(0.864, color=INK, lw=1.2, ls=(0, (3, 3)))
ax.text(-0.1, 0.867, "Topping baseline 86%", fontsize=9.5, color=INK, va="bottom")
ax.set_xticks(list(x), bands); ax.set_xlim(-0.3, 5.5); ax.set_ylim(0.70, 0.92)
ax.set_yticks([0.70, 0.74, 0.78, 0.82, 0.86, 0.90])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0)); grid_y(ax)
ax.set_xlabel("ARPU uplift band  ((ARPU after - ARPU before) / ARPU before)"); ax.set_ylabel("M06 survival rate")
ax.legend(frameon=False, loc="lower left", fontsize=10)
title(ax, "The harder the bill jumps, the faster customers leave",
      "OTT topping sold by Contact Center - M06 survival by ARPU-uplift band")
save(fig, "05_arpu_uplift_band.png")

sb = [">+10pp", "+5 to +10", "+2 to +5", "0 to +2", "-2 to 0", "-5 to -2", "-10 to -5", "<-10pp"]
share = [.03, .06, .11, .17, .18, .17, .19, .09]
cols = ["#184f95", "#2a78d6", "#6da7ec", "#b7d3f6", "#f6c9c8", "#ee9a99", "#e34948", "#b83232"]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(sb, share, color=cols, edgecolor=SURF, linewidth=2, width=0.72, zorder=2)
for i, s_ in enumerate(share):
    ax.text(i, s_ + 0.004, f"{s_:.0%}", ha="center", fontsize=10, color=INK2)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0)); ax.set_ylim(0, 0.23); grid_y(ax)
ax.set_xlabel("Agent score = agent's M06 survival - topping baseline (86%)"); ax.set_ylabel("Share of OTT topping sales")
ax.text(1.5, 0.205, "<- Better than baseline", ha="center", fontsize=10, color=INK2, fontweight="bold")
ax.text(5.5, 0.215, "Worse than baseline ->", ha="center", fontsize=10, color=INK2, fontweight="bold")
title(ax, "45% of contact-center OTT sales come from agents 2pp+ below baseline",
      "Seller-quality scoring across ~900 contact-center agents (aggregated bands only)")
save(fig, "06_seller_quality_distribution.png")

rows = [("Brand A", .869, .902, .905), ("Brand B", .905, .921, .931), ("Both brands", .881, .919, .914)]
fig, ax = plt.subplots(figsize=(9, 3.8))
for i, (lab, before, after, base) in enumerate(rows[::-1]):
    ax.plot([before, after], [i, i], color=AXIS, lw=3, zorder=1)
    ax.scatter(before, i, s=90, color=GRAY, zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.scatter(after, i, s=90, color=BLUE, zorder=3, edgecolor=SURF, linewidth=1.5)
    ax.scatter(base, i, s=160, marker="|", color=INK, zorder=4, linewidth=2)
    ax.text(before - 0.003, i + 0.22, f"{before:.1%}", ha="center", fontsize=9.5, color=INK2)
    ax.text(after + 0.003, i + 0.22, f"{after:.1%}", ha="center", fontsize=9.5, color=BLUE)
    ax.text(0.952, i, f"gap {(before-base)*100:+.1f}pp -> {(after-base)*100:+.1f}pp", va="center", fontsize=10, color=INK)
ax.set_yticks(range(3), [r[0] for r in rows[::-1]])
ax.set_xlim(0.86, 0.99); ax.set_ylim(-0.6, 2.7); ax.set_xticks([0.86, 0.88, 0.90, 0.92, 0.94])
ax.spines["bottom"].set_bounds(0.86, 0.945)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0)); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.scatter([], [], color=GRAY, s=60, label="OTT today"); ax.scatter([], [], color=BLUE, s=60, label="OTT after excluding risky segments")
ax.scatter([], [], marker="|", color=INK, s=100, label="Non-digital baseline")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.18), ncol=3, fontsize=9.5)
title(ax, "Cutting the risky segments closes the survival gap",
      "M06 survival - OTT buyers vs non-digital users, before and after applying the recommended sales guardrails")
save(fig, "07_impact_survival_gap.png")
print("done")
