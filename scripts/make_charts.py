import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl

REPORT = Path("data/eval/report.json")
ABLATION = Path("data/eval/ablation.json")
ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)

INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#E5E7EB"
ACCENT = "#2851A3"
GOOD = "#0F766E"
WARN = "#B45309"
BG = "#FAFAFA"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10.5,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.labelsize": 10,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "grid.alpha": 1.0,
    "axes.axisbelow": True,
    "figure.facecolor": BG,
})


def _frame(ax):
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.7)
    ax.tick_params(length=0)


def _titles(fig, title, subtitle=None):
    fig.text(0.04, 0.965, title, fontsize=14, fontweight="semibold",
             color=INK, ha="left", va="top")
    if subtitle:
        fig.text(0.04, 0.918, subtitle, fontsize=10.5, color=MUTED,
                 ha="left", va="top")


def eval_summary():
    data = json.loads(REPORT.read_text())
    m = data["metrics"]
    labels = ["Recall@5", "Correctness", "Faithfulness"]
    values = [m["recall_at_5"], m["correctness"], m.get("faithfulness", 0)]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.set_facecolor(BG)
    bars = ax.bar(labels, values, color=ACCENT, width=0.5, edgecolor="none")
    bars[0].set_color(GOOD)
    bars[2].set_color(GOOD)

    ax.set_ylim(0, 1.10)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax.set_ylabel("score", color=MUTED)

    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.022, f"{v:.1%}",
                ha="center", color=INK, fontsize=11.5, fontweight="semibold")

    _frame(ax)
    fig.subplots_adjust(top=0.80, left=0.10, right=0.96, bottom=0.12)
    _titles(fig, f"RAG evaluation — {m['total']} questions",
            "Llama 3.3 70B as judge · retrieval, correctness, faithfulness")
    fig.savefig(ASSETS / "eval_summary.png", dpi=160, facecolor=BG)
    plt.close(fig)


def eval_by_category():
    data = json.loads(REPORT.read_text())
    rows = data["details"]
    cats = {}
    for r in rows:
        c = r["category"]
        cats.setdefault(c, {"recall": [], "correct": []})
        cats[c]["recall"].append(r["source_recall"])
        cats[c]["correct"].append(r["correctness"])

    names = sorted(cats)
    rec = [sum(cats[c]["recall"]) / len(cats[c]["recall"]) for c in names]
    cor = [sum(cats[c]["correct"]) / len(cats[c]["correct"]) for c in names]

    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.set_facecolor(BG)
    x = list(range(len(names)))
    width = 0.38
    ax.bar([i - width / 2 for i in x], rec, width,
           label="Recall@5", color=GOOD, edgecolor="none")
    ax.bar([i + width / 2 for i in x], cor, width,
           label="Correctness", color=ACCENT, edgecolor="none")

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylim(0, 1.10)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax.set_ylabel("score", color=MUTED)

    leg = ax.legend(frameon=False, loc="lower right", fontsize=10)
    for t in leg.get_texts():
        t.set_color(INK)

    _frame(ax)
    fig.subplots_adjust(top=0.84, left=0.07, right=0.97, bottom=0.22)
    _titles(fig, "Per-category performance",
            "Recall@5 and Correctness across 12 question categories")
    fig.savefig(ASSETS / "eval_by_category.png", dpi=160, facecolor=BG)
    plt.close(fig)


def ablation_chart():
    if not ABLATION.exists():
        return
    data = json.loads(ABLATION.read_text())
    names = list(data.keys())
    pretty = [n.replace("_", " ") for n in names]
    recall = [data[n]["recall_at_5"] for n in names]
    latency = [data[n]["avg_retrieval_ms"] for n in names]

    fig, ax1 = plt.subplots(figsize=(8.6, 4.6))
    ax1.set_facecolor(BG)
    ax2 = ax1.twinx()
    ax2.set_facecolor(BG)

    bars = ax1.bar(pretty, recall, color=GOOD, width=0.42,
                   edgecolor="none", label="Recall@5", zorder=2)
    ax2.plot(pretty, latency, "o-", color=WARN, linewidth=2.0,
             markersize=8, label="latency", zorder=3)

    ax1.set_ylim(0, 1.18)
    ax1.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax1.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax1.set_ylabel("Recall@5", color=MUTED)
    ax2.set_ylabel("avg retrieval, ms", color=MUTED)
    ax2.set_ylim(0, max(latency) * 1.45)

    for b, v in zip(bars, recall):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.025, f"{v:.1%}",
                 ha="center", color=INK, fontsize=11, fontweight="semibold")
    for x_i, y in zip(pretty, latency):
        ax2.text(x_i, y + max(latency) * 0.06, f"{y:.0f} ms",
                 ha="center", color=WARN, fontsize=10, fontweight="semibold")

    _frame(ax1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color(MUTED)
    ax2.spines["right"].set_linewidth(0.7)
    ax2.tick_params(length=0)
    ax1.grid(axis="x", visible=False)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    leg = ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="lower center",
                     bbox_to_anchor=(0.5, -0.20), ncol=2, fontsize=10)
    for t in leg.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(top=0.82, left=0.09, right=0.91, bottom=0.20)
    _titles(fig, "Ablation: vector — hybrid — reranked",
            "Each step in the retrieval pipeline and what it costs in latency")
    fig.savefig(ASSETS / "ablation.png", dpi=160, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    eval_summary()
    eval_by_category()
    ablation_chart()
    print("Charts saved to", ASSETS)
