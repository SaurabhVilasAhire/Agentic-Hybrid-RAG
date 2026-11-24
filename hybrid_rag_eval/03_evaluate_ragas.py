"""
Step 3: Score results.json with RAGAS (faithfulness, answer relevancy,
context precision, context recall), broken down by question category.

Uses your local qwen2.5:7b (via Ollama) as the judge LLM, so this runs
fully offline, no OpenAI key needed. It will be slower and slightly
less reliable than GPT-4o-mini as a judge, but it is free and private.

Usage:
    python 03_evaluate_ragas.py --results results.json --out ragas_scores.json
"""

import argparse
import json

import pandas as pd
from datasets import Dataset
from langchain_ollama import ChatOllama, OllamaEmbeddings
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)


def build_ragas_dataset(results: list):
    return Dataset.from_dict({
        "question": [r["question"] for r in results],
        "answer": [r["answer"] for r in results],
        "contexts": [r["contexts"] if r["contexts"] else [""] for r in results],
        "ground_truth": [r["gold_answer"] for r in results],
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=str, default="results.json")
    parser.add_argument("--out", type=str, default="ragas_scores.json")
    parser.add_argument("--judge_model", type=str, default="qwen2.5:7b")
    parser.add_argument("--embed_model", type=str, default="mxbai-embed-large")
    args = parser.parse_args()

    with open(args.results, "r", encoding="utf-8") as f:
        results = json.load(f)

    print(f"Loaded {len(results)} results.")

    judge_llm = ChatOllama(model=args.judge_model, temperature=0)
    judge_embeddings = OllamaEmbeddings(model=args.embed_model)

    dataset = build_ragas_dataset(results)

    # Local CPU-only models are slow, especially since each RAGAS metric
    # can involve multiple sequential internal LLM calls (faithfulness
    # breaks the answer into statements, then verifies each one).
    # A long timeout and max_workers=1 avoids the default timeout and
    # avoids flooding a single local Ollama instance with parallel calls
    # it can't actually run in parallel anyway.
    run_config = RunConfig(timeout=1200, max_workers=1)

    print("Running RAGAS evaluation (this can take a while on local models)...")
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_embeddings,
        run_config=run_config,
    )

    scores_df = scores.to_pandas()
    scores_df["category"] = [r["category"] for r in results]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scores_df.to_dict(orient="records"), f, indent=2)

    print("\n=== OVERALL SCORES ===")
    print(scores_df[["faithfulness", "answer_relevancy",
                      "context_precision", "context_recall"]].mean().round(3))

    print("\n=== SCORES BY CATEGORY ===")
    print(scores_df.groupby("category")[[
        "faithfulness", "answer_relevancy", "context_precision", "context_recall"
    ]].mean().round(3))

    print(f"\nFull per-question scores saved to {args.out}")


if __name__ == "__main__":
    main()