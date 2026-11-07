"""Figure 1: where fishtrap acts in a long Codex session."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import sys
LANG = sys.argv[2] if len(sys.argv) > 2 else "en"

plt.rcParams.update({"font.family": ["Helvetica", "Hiragino Sans GB"] if LANG == "en" else ["Hiragino Sans GB"], "font.size": 8.5, "pdf.fonttype": 42})
INK, MUTED, ACCENT, BAND, ZONE = "#1f2933", "#6b7280", "#b4540a", "#2f5d8a", "#f3e7da"

fig, ax = plt.subplots(figsize=(7.0, 3.0))
fig.patch.set_facecolor("white")
ax.set_xlim(0, 100)
ax.set_ylim(0, 50)
ax.axis("off")

# principles band: read at session start, fades with distance
grad = np.linspace(1.0, 0.18, 400).reshape(1, -1)
ax.imshow(grad, extent=(3, 97, 44, 48), aspect="auto", cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
    "b", ["#ffffff", BAND]), vmin=0, vmax=1, zorder=1)
ax.text(4, 46, "AGENTS.md principles: loaded at session start; the motivating photo uploads came at tool call 114" if LANG == "en" else "AGENTS.md 原则在会话开始时读入；促成本项目的照片上传发生在第 114 次工具调用",
        color="white", va="center", fontsize=8, fontweight="bold", zorder=2)

# outbound boundary zone
ax.add_patch(Rectangle((56.5, 3.2), 26.5, 38.5, facecolor=ZONE, edgecolor="none", zorder=0))
ax.text(69.75, 0.6, "outbound boundary" if LANG == "en" else "对外边界", ha="center", color=ACCENT, fontsize=7.5, style="italic")

# timeline
ax.annotate("", xy=(97, 22), xytext=(3, 22), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
ax.text(3, 19.2, "session time (tool calls)" if LANG == "en" else "会话进程（工具调用）", ha="left", color=MUTED, fontsize=7.5)

hooks = [
    (6, "UserPromptSubmit", "store the brief; restate it when a\nturn adds a count, continues, or unblocks"),
    (25, "SessionStart", "after compaction or resume:\nrestate the brief; old precautions\nare working assumptions"),
    (45, "PostToolUse", "after a validation message:\nfix it the way the\nreviewer would want"),
    (64, "PreToolUse: upload", "recipient check: what will\nthe reader see in this\nfile name and content?"),
    (78, "PreToolUse: submit/send", "readback against\nthe request before\nit leaves"),
    (92, "Stop", "closure check:\nevery part done,\nparked work resumed"),
]
hooks_zh = [
    (6, "UserPromptSubmit", "记住最初的需求；新指令带数字、\n“继续”或“解锁了”时重申它"),
    (25, "SessionStart", "压缩或恢复会话后：\n重申需求；早先的谨慎\n只是工作假设"),
    (45, "PostToolUse", "看到校验提示后：\n按审核人想要的\n方式修正"),
    (64, "PreToolUse: 上传", "收件人检查：对方会\n从这个文件名和内容里\n看到什么？"),
    (78, "PreToolUse: 提交/发送", "提交前对照\n原始需求\n复读一遍"),
    (92, "Stop", "收尾检查：\n每一项都做完，\n搁置的已恢复"),
]
if LANG != "en":
    hooks = hooks_zh
for i, (x, name, what) in enumerate(hooks):
    up = i % 2 == 0
    ax.plot([x, x], [22, 26.5 if up else 17.5], color=ACCENT, lw=1)
    ax.plot(x, 22, "o", ms=6.5, mfc="white", mec=ACCENT, mew=1.6, zorder=3)
    if up:
        ax.text(x, 27.3, name, ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=INK)
        ax.text(x, 30.0, what, ha="center", va="bottom", fontsize=6.6, color=MUTED, linespacing=1.15)
    else:
        ax.text(x, 16.7, name, ha="center", va="top", fontsize=7.8, fontweight="bold", color=INK)
        ax.text(x, 13.9, what, ha="center", va="top", fontsize=6.6, color=MUTED, linespacing=1.15)

fig.savefig(sys.argv[1], bbox_inches="tight", pad_inches=0.04)
print("wrote", sys.argv[1])
