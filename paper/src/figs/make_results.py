"""Result figures for the paper (PDF) and the README (SVG, English and Chinese).
usage: make_results.py <final_results.json> <paper figs dir> <repo assets dir>
"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

R, FIGS, ASSETS = sys.argv[1:4]
d = json.load(open(R))
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e2dc"
BLUE, GRAY = "#2a78d6", "#8f8d86"
SEQ = ["#e9f1fb", "#9ec5f4", "#5598e7", "#1c5cab"]  # 0/3 .. 3/3 passed
ORDER = ["N", "H", "P", "F"]
COLOR = {"N": GRAY, "H": GRAY, "P": BLUE, "F": BLUE}
HOLLOW = {"H", "F"}
LABEL = {"en": {"N": "N  none", "H": "H  hooks only", "P": "P  principles", "F": "F  principles + hooks"},
         "zh": {"N": "N  不加", "H": "H  只加 hook", "P": "P  只加原则", "F": "F  原则 + hook"}}
TITLES = {"en": ["Passed all retained checks\nhigher is better", "Failed a trap check\nlower is better",
                 "Failed a guard check\nlower is better"],
          "zh": ["保留的检查全部通过\n越高越好", "未通过陷阱检查\n越低越好", "未通过防护检查\n越低越好"]}
METRICS = ["audited_pass", "trap_fail", "guard_fail"]


def style(lang):
    fam = ["Helvetica", "Hiragino Sans GB"] if lang == "en" else ["Hiragino Sans GB"]
    plt.rcParams.update({"font.family": fam, "font.size": 8.5, "pdf.fonttype": 42, "svg.fonttype": "path",
                         "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK,
                         "figure.facecolor": SURF, "axes.facecolor": SURF})


def dots(lang, out, part="all", note=None):
    style(lang)
    arms = d[part]["arms"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), sharey=True)
    fig.subplots_adjust(wspace=0.12)
    for k, (ax, m) in enumerate(zip(axes, METRICS)):
        for i, a in enumerate(ORDER):
            y = len(ORDER) - 1 - i
            v, (lo, hi) = arms[a][m], arms[a][m + "_ci"]
            ax.plot([lo * 100, hi * 100], [y, y], color=COLOR[a], lw=2, solid_capstyle="round", zorder=2)
            ax.plot(v * 100, y, "o", ms=8, mfc=SURF if a in HOLLOW else COLOR[a], mec=COLOR[a], mew=2, zorder=3)
            ax.text(hi * 100 + 3, y, f"{v * 100:.0f}%", va="center", fontsize=8, color=INK)
        ax.set_xlim(0, 112)
        ax.set_xticks([0, 50, 100])
        ax.set_xticklabels(["0", "50", "100%"])
        ax.grid(axis="x", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_title(TITLES[lang][k], fontsize=8.5, color=INK, loc="left", pad=6, linespacing=1.3)
    axes[0].set_yticks(range(len(ORDER)))
    axes[0].set_yticklabels([LABEL[lang][a] for a in reversed(ORDER)])
    axes[0].set_ylim(-0.6, len(ORDER) - 0.4)
    if note:
        fig.text(0.0, -0.06, note, fontsize=7.2, color=INK2, ha="left")
    fig.savefig(out, bbox_inches="tight", pad_inches=0.05, facecolor=SURF)
    plt.close(fig)
    print("wrote", out)


def heatmap(out):
    style("en")
    ids = sorted(d["by_scenario"], key=lambda s: (s[0] == "L", int(s[1:])))
    fig, ax = plt.subplots(figsize=(3.3, 5.2))
    cmap = ListedColormap(SEQ)
    grid = [[round(d["by_scenario"][s][a]["audited_pass"] * 3) for a in ORDER] for s in ids]
    ax.imshow(grid, cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    for r, s in enumerate(ids):
        for c, a in enumerate(ORDER):
            v = grid[r][c]
            ax.text(c, r, f"{v}/3", ha="center", va="center", fontsize=7.5, color="white" if v >= 2 else INK)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["N\nnone", "H\nhooks", "P\nprinc.", "F\nboth"], fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(ids)))
    ax.set_yticklabels(ids, fontsize=8)
    ax.set_xticks([x - 0.5 for x in range(1, 4)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(ids))], minor=True)
    ax.grid(which="minor", color=SURF, lw=2)
    ax.axhline(15.5, color=INK2, lw=1)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.05, facecolor=SURF)
    plt.close(fig)
    print("wrote", out)


def cost(out):
    style("en")
    rows = d["rows"]
    arms = {a: {m: sum(r[m] for r in rows if r["arm"] == a) / sum(1 for r in rows if r["arm"] == a)
                for m in ("out_tok", "sec")} for a in ORDER}   # unrounded means
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 1.7), sharey=True)
    for ax, (m, title, scale, unit) in zip(axes, [("out_tok", "Output tokens per run", 1000, "k"),
                                                  ("sec", "Wall-clock time per run", 1, " s")]):
        base = arms["N"][m]
        for i, a in enumerate(ORDER):
            y = len(ORDER) - 1 - i
            v = arms[a][m]
            ax.barh(y, v / scale, height=0.55, color=COLOR[a], alpha=1 if a not in HOLLOW else 0.45)
            rel = "" if a == "N" else f"  ({(v / base - 1) * 100:+.0f}%)"
            ax.text(v / scale * 1.02, y, f"{v / scale:.1f}{unit}{rel}" if scale > 1 else f"{v:.0f}{unit}{rel}",
                    va="center", fontsize=7.5, color=INK)
        ax.set_title(title, fontsize=8.5, loc="left", color=INK)
        ax.set_xlim(0, max(arms[a][m] for a in ORDER) / scale * 1.55)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(4))
    axes[0].set_yticklabels([LABEL["en"][a] for a in reversed(ORDER)])
    fig.savefig(out, bbox_inches="tight", pad_inches=0.05, facecolor=SURF)
    plt.close(fig)
    print("wrote", out)


n = d["all"]["arms"]["N"]["n"]
dots("en", FIGS + "/results_main.pdf")
dots("en", FIGS + "/results_long.pdf", part="long")
dots("en", ASSETS + "/results.svg", note=f"GPT-6.1 in Codex, 20 scenarios × 3 runs = {n} runs per condition. Guard checks fail over-correction. Bars: 95% Wilson intervals. Hollow: hooks on.")
dots("zh", ASSETS + "/results.zh-CN.svg", note=f"Codex 中的 GPT-6.1，20 个场景 × 3 次 = 每组 {n} 次运行。防护检查判定矫枉过正。横线为 95% Wilson 区间；空心点表示开了 hook。")
heatmap(FIGS + "/heatmap.pdf")
cost(FIGS + "/cost.pdf")
