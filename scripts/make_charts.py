import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl

REPORT = Path("data/eval/report.json")
ABLATION = Path("data/eval/ablation.json")
ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)

NAVY = "#1F2A44"
TEAL = "#2A9D8F"
AMBER = "#E9C46A"
CORAL = "#E76F51"
SLATE = "#264653"
GRID = "#E5E7EB"
TEXT = "#1F2937"
MUTED = "#6B7280"
BG = "#FAFAF7"

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": MUTED,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "axes.titlesize": 13,
    "axes.titleweight": "semibold",
    "axes.titlepad": 14,
    "axes.labelsize": 10.5,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "grid.alpha": 1.0,
    "axes.axisbelow": True,
})


def _frame(ax):
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(length=0)
    ax.grid(axis="x", visible=False)


def eval_summary():
    data = json.loads(REPORT.read_text())
    m = data["metrics"]
    labels = ["Recall@5", "Correctness", "Faithfulness"]
    values = [m["recall_at_5"], m["correctness"], m.get("faithfulness", 0)]
    colors = [TEAL, AMBER, CORAL]

    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor=BG)
    ax.set_facecolor(BG)
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="none")
    ax.set_ylim(0, 1.08)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax.set_ylabel("score", color=MUTED)
    ax.set_title(f"RAG evaluation  ·  {m['total']} questions  ·  Llama 3.3 70B judge", loc="left")
    for b, v in zip(bars, values):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 0.018,
            f"{v:.1%}",
            ha="center",
            color=TEXT,
            fontsize=11,
            fontweight="semibold",
        )
    _frame(ax)
    fig.tight_layout()
    fig.savefig(ASSETS / "eval_summary.png", dpi=140, facecolor=BG)
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

    fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=BG)
    ax.set_facecolor(BG)
    x = list(range(len(names)))
    width = 0.38
    ax.bar([i - width / 2 for i in x], rec, width, label="Recall@5", color=TEAL, edgecolor="none")
    ax.bar([i + width / 2 for i in x], cor, width, label="Correctness", color=AMBER, edgecolor="none")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax.set_ylabel("score", color=MUTED)
    ax.set_title("Per-category performance", loc="left")
    leg = ax.legend(frameon=False, loc="lower right", fontsize=10)
    for t in leg.get_texts():
        t.set_color(TEXT)
    _frame(ax)
    fig.tight_layout()
    fig.savefig(ASSETS / "eval_by_category.png", dpi=140, facecolor=BG)
    plt.close(fig)


def ablation_chart():
    if not ABLATION.exists():
        return
    data = json.loads(ABLATION.read_text())
    names = list(data.keys())
    pretty = [n.replace("_", " ") for n in names]
    recall = [data[n]["recall_at_5"] for n in names]
    latency = [data[n]["avg_retrieval_ms"] for n in names]

    fig, ax1 = plt.subplots(figsize=(8.2, 4.6), facecolor=BG)
    ax1.set_facecolor(BG)
    ax2 = ax1.twinx()
    ax2.set_facecolor(BG)

    bars = ax1.bar(pretty, recall, color=TEAL, width=0.42, edgecolor="none", label="Recall@5", zorder=2)
    ax2.plot(pretty, latency, "o-", color=CORAL, linewidth=2.2, markersize=8, label="Latency (ms)", zorder=3)

    ax1.set_ylim(0, 1.18)
    ax1.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax1.set_yticklabels(["25%", "50%", "75%", "100%"])
    ax1.set_ylabel("Recall@5", color=MUTED)
    ax2.set_ylabel("avg retrieval, ms", color=MUTED)
    ax2.set_ylim(0, max(latency) * 1.4)

    for b, v in zip(bars, recall):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.022, f"{v:.1%}",
                 ha="center", color=TEXT, fontsize=10, fontweight="semibold")
    for x_i, y in zip(pretty, latency):
        ax2.text(x_i, y + max(latency) * 0.06, f"{y:.0f} ms",
                 ha="center", color=CORAL, fontsize=9.5, fontweight="semibold")

    ax1.set_title("Ablation  ·  vector  →  hybrid (RRF)  →  hybrid + cross-encoder rerank", loc="left")
    _frame(ax1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color(MUTED)
    ax2.spines["right"].set_linewidth(0.8)
    ax2.tick_params(length=0)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    leg = ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="lower center",
                     bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=10)
    for t in leg.get_texts():
        t.set_color(TEXT)
    fig.subplots_adjust(bottom=0.18)

    fig.tight_layout()
    fig.savefig(ASSETS / "ablation.png", dpi=140, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    eval_summary()
    eval_by_category()
    ablation_chart()
    print("Charts saved to assets/")
