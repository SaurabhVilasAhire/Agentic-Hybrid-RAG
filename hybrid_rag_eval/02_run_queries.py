"""
Step 2: Run every question from questions.json through your LIVE running
pipeline (the FastAPI backend on localhost:8000) and log question,
retrieved context, generated answer, and category.

IMPORTANT before running this:
  1. Your backend must be running (uvicorn backend.main:APP ...)
  2. Your two watchers must have finished ingesting every file from
     01_download_hotpotqa.py into Neo4j and FAISS. Give it a minute
     after dropping in ~60 files.
  3. The exact response field names below (answer / context) are a
     best guess based on the repo's structure. The FIRST time you run
     this script, it will print the raw JSON response for question 1
     and pause, so you can confirm or fix the field names before it
     burns through all 60 queries. Check http://localhost:8000/docs
     if you want to look at the schema directly.

Usage:
    python 02_run_queries.py --questions questions.json --out results.json
"""

import argparse
import json
import time
from pathlib import Path

import requests
from tqdm import tqdm

API_URL = "http://localhost:8000/query"


def call_pipeline(question: str, bypass_cache: bool = True):
    """
    Sends one question to your running backend.
    bypass_cache=True is important for eval: you want a fresh retrieval
    for every question, not a cached answer from a previous run.
    """
    payload = {
        "query": question,
        "conversation_id": "eval_run",
        "mode": "concise",
        "max_tokens": 512,
        "temperature": 0,
        "top_k": 5,
        "bypass_cache": bypass_cache,
    }
    response = requests.post(API_URL, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


def extract_fields(raw_response: dict):
    """
    Matches the confirmed backend schema:
      answer: top-level string
      sources: list of {text, score, metadata, source, chunk_id}
    We pull the "text" field out of each source to build the RAGAS
    contexts list.
    """
    answer = raw_response.get("answer", "")
    sources = raw_response.get("sources", []) or []
    contexts = [s.get("text", "") for s in sources if s.get("text")]
    return answer, contexts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=str, default="questions.json")
    parser.add_argument("--out", type=str, default="results.json")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds to wait between queries, be kind to your local LLM")
    args = parser.parse_args()

    with open(args.questions, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions.")
    print("Sending question 1 first, to confirm the response format...\n")

    first = questions[0]
    raw = call_pipeline(first["question"])
    print("RAW RESPONSE FOR QUESTION 1:")
    print(json.dumps(raw, indent=2)[:1500])
    print("\nIf 'answer' and 'context' below look empty or wrong, stop here,")
    print("open this script, and fix extract_fields() to match the real keys above.\n")

    answer, contexts = extract_fields(raw)
    print(f"Extracted answer: {answer[:200]}")
    print(f"Extracted contexts ({len(contexts)}): {contexts[:1] if contexts else 'NONE FOUND'}")

    proceed = input("\nDoes this look right? Type 'y' to continue with all questions: ")
    if proceed.strip().lower() != "y":
        print("Stopped. Fix extract_fields() and re-run.")
        return

    results = [{
        "id": first["id"],
        "question": first["question"],
        "gold_answer": first["gold_answer"],
        "category": first["category"],
        "answer": answer,
        "contexts": contexts,
    }]

    for q in tqdm(questions[1:], desc="Running queries"):
        try:
            raw = call_pipeline(q["question"])
            answer, contexts = extract_fields(raw)
        except Exception as e:
            print(f"\nFailed on {q['id']}: {e}")
            answer, contexts = "", []

        results.append({
            "id": q["id"],
            "question": q["question"],
            "gold_answer": q["gold_answer"],
            "category": q["category"],
            "answer": answer,
            "contexts": contexts,
        })
        time.sleep(args.delay)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    empty_context_count = sum(1 for r in results if not r["contexts"])
    print(f"\nDone. {len(results)} results saved to {args.out}")
    if empty_context_count:
        print(f"WARNING: {empty_context_count} results had empty contexts, "
              f"double check extract_fields() field names.")


if __name__ == "__main__":
    main()