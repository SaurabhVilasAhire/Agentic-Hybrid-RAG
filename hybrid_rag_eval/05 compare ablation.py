"""
Step 5: Compare hybrid vs vector-only vs graph-only RAGAS scores,
broken down by question category, and produce a bar chart.

This is the script that produces your actual CV-worthy result.

Usage:
    python 05_compare_ablation.py \
        --hybrid ragas_hybrid.json \
        --vector_only ragas_vector_only.json \
        --graph_only ragas_graph_only.json \
        --out_chart ablation_comparison.png
"""

import argparse
import json

import matplotlib.pyplot as plt
import pandas as pd

METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def load_scores(path: str, variant_name: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["variant"] = variant_name
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hybrid", type=str, default="ragas_hybrid.json")
    parser.add_argument("--vector_only", type=str, default="ragas_vector_only.json")
    parser.add_argument("--graph_only", type=str, default="ragas_graph_only.json")
    parser.add_argument("--out_chart", type=str, default="ablation_comparison.png")
    parser.add_argument("--out_table", type=str, default="ablation_comparison.csv")
    args = parser.parse_args()

    hybrid = load_scores(args.hybrid, "Hybrid")
    vector_only = load_scores(args.vector_only, "Vector-only")
    graph_only = load_scores(args.graph_only, "Graph-only")

    combined = pd.concat([hybrid, vector_only, graph_only], ignore_index=True)

    overall = combined.groupby("variant")[METRICS].mean().round(3)
    print("\n=== OVERALL COMPARISON ===")
    print(overall)

    by_category = combined.groupby(["variant", "category"])[METRICS].mean().round(3)
    print("\n=== BY CATEGORY ===")
    print(by_category)

    overall.to_csv(args.out_table)
    print(f"\nOverall comparison table saved to {args.out_table}")

    fig, ax = plt.subplots(figsize=(10, 6))
    overall.T.plot(kind="bar", ax=ax)
    ax.set_ylabel("Score (0 to 1)")
    ax.set_title("Hybrid vs Vector-only vs Graph-only RAG, RAGAS metrics")
    ax.set_ylim(0, 1)
    ax.legend(title="Retrieval mode")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(args.out_chart, dpi=150)
    print(f"Chart saved to {args.out_chart}")


if __name__ == "__main__":
    main()