import json
from pathlib import Path

import matplotlib.pyplot as plt

REPORT = Path("data/eval/report.json")
ABLATION = Path("data/eval/ablation.json")
ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)


def eval_summary():
    data = json.loads(REPORT.read_text())
    m = data["metrics"]
    labels = ["Recall@5", "Correctness", "Faithfulness"]
    values = [m["recall_at_5"], m["correctness"], m.get("faithfulness", 0)]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(labels, values, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score")
    ax.set_title(f"RAG eval ({m['total']} questions)")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.1%}", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(ASSETS / "eval_summary.png", dpi=120)
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

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(names))
    width = 0.4
    ax.bar([i - width / 2 for i in x], rec, width, label="Recall@5", color="#4C72B0")
    ax.bar([i + width / 2 for i in x], cor, width, label="Correctness", color="#55A868")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score")
    ax.set_title("Per-category scores")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ASSETS / "eval_by_category.png", dpi=120)
    plt.close(fig)


def ablation_chart():
    if not ABLATION.exists():
        return
    data = json.loads(ABLATION.read_text())
    names = list(data.keys())
    recall = [data[n]["recall_at_5"] for n in names]
    latency = [data[n]["avg_retrieval_ms"] for n in names]

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax2 = ax1.twinx()
    ax1.bar(names, recall, color="#4C72B0", alpha=0.8, label="Recall@5")
    ax2.plot(names, latency, "o-", color="#C44E52", label="Latency (ms)")
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("Recall@5")
    ax2.set_ylabel("avg retrieval, ms")
    ax1.set_title("Ablation: vector vs hybrid vs hybrid+rerank")
    fig.tight_layout()
    fig.savefig(ASSETS / "ablation.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    eval_summary()
    eval_by_category()
    ablation_chart()
    print("Charts saved to assets/")
