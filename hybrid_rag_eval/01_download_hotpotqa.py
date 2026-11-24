"""
Step 1: Download a small slice of HotpotQA, save the context paragraphs
as .txt files (your test corpus), and save a tagged question set (JSON)
for later evaluation.

Run this once, before anything else.

Usage:
    python 01_download_hotpotqa.py --n 60 --out_dir ../agentic-graph-rag/knowledge --questions_out questions.json
"""

import argparse
import json
import os
import random
from pathlib import Path

from datasets import load_dataset


def build_question_record(example, idx):
    """
    Turn one HotpotQA example into our tagged format.
    hop_count = number of distinct supporting titles = proxy for single-hop vs multi-hop.
    """
    supporting_titles = sorted(set(example["supporting_facts"]["title"]))
    hop_count = len(supporting_titles)

    if hop_count <= 1:
        category = "single_hop"
    elif example.get("type") == "comparison":
        category = "comparison"
    else:
        category = "multi_hop"

    return {
        "id": f"hotpot_{idx}",
        "question": example["question"],
        "gold_answer": example["answer"],
        "supporting_titles": supporting_titles,
        "hop_count": hop_count,
        "category": category,
    }


def save_contexts_as_txt(example, out_dir: Path, seen_titles: set):
    """
    HotpotQA gives you a list of [title, sentences] pairs per example.
    We save each unique title once as its own .txt file, this becomes
    what your ingestion watchers pick up.
    """
    titles = example["context"]["title"]
    sentences_list = example["context"]["sentences"]

    for title, sentences in zip(titles, sentences_list):
        if title in seen_titles:
            continue
        seen_titles.add(title)

        safe_name = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in title)
        safe_name = safe_name.strip().replace(" ", "_")[:80]
        file_path = out_dir / f"{safe_name}.txt"

        text = " ".join(sentences)
        file_path.write_text(f"{title}\n\n{text}", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=60,
                        help="Number of questions to sample")
    parser.add_argument("--out_dir", type=str, default="knowledge",
                        help="Folder to write context .txt files into (your repo's knowledge/ folder)")
    parser.add_argument("--questions_out", type=str, default="questions.json",
                        help="Where to save the tagged question set")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading HotpotQA (distractor, validation split)...")
    dataset = load_dataset("hotpot_qa", "distractor", split="validation", trust_remote_code=True)

    random.seed(args.seed)
    indices = random.sample(range(len(dataset)), args.n)

    questions = []
    seen_titles = set()

    for idx in indices:
        example = dataset[idx]
        questions.append(build_question_record(example, idx))
        save_contexts_as_txt(example, out_dir, seen_titles)

    with open(args.questions_out, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    by_category = {}
    for q in questions:
        by_category[q["category"]] = by_category.get(q["category"], 0) + 1

    print(f"\nDone.")
    print(f"  {len(questions)} questions saved to {args.questions_out}")
    print(f"  {len(seen_titles)} context files written to {out_dir}/")
    print(f"  Category breakdown: {by_category}")
    print(f"\nNext: let your two ingestion watchers pick up every file in {out_dir}/")
    print(f"before running 02_run_queries.py")


if __name__ == "__main__":
    main()