# Hybrid RAG Evaluation Toolkit

Evaluates the agentic-graph-rag pipeline on a real benchmark (HotpotQA)
using RAGAS metrics, with a hybrid vs vector-only vs graph-only ablation.

## Before you start

Your pipeline must already be fully running:
- Neo4j up (`docker ps` shows it)
- Ollama running with `qwen2.5:7b` and `mxbai-embed-large` pulled
- Both ingestion watchers running
- Backend running on `localhost:8000`
- (Chainlit frontend is optional for this, we talk to the backend API directly)

## Setup

```bash
cd hybrid_rag_eval
pip install -r requirements-eval.txt --break-system-packages
```

## Step by step

### 1. Download the benchmark and build your test corpus

```bash
python 01_download_hotpotqa.py --n 60 --out_dir ../agentic-graph-rag/knowledge --questions_out questions.json
```

This drops ~60 questions worth of Wikipedia paragraphs straight into
your repo's `knowledge/` folder. Your two watcher terminals should
start printing ingestion activity within a few seconds, since Docker/
Ollama/watchers are already running from earlier.

**Wait for ingestion to finish** before moving on. With ~60 questions
you'll get somewhere around 150-250 unique context files (HotpotQA
gives 10 paragraphs per question, several overlap). Give it a few
minutes, check your watcher terminals stop printing new activity.

### 2. Run every question through your live pipeline

```bash
python 02_run_queries.py --questions questions.json --out results.json
```

This pauses after question 1 and shows you the raw API response, so
you can confirm the script is reading the right fields (`answer`,
`context`) before it runs through all 60. If the extracted answer/
context look wrong, open `02_run_queries.py`, find `extract_fields()`,
and match the key names to what you see printed.

This takes a while, local LLM inference on ~60 questions with a retry
loop that can run up to 7 iterations per question is not fast. Let it run.

### 3. Score with RAGAS

```bash
python 03_evaluate_ragas.py --results results.json --out ragas_scores.json
```

Prints overall scores and a breakdown by category (single_hop,
multi_hop, comparison) straight to your terminal, and saves the full
per-question scores to `ragas_scores.json`.

This is a real, reportable result on its own: something like
"faithfulness 0.82, context recall 0.71 on a 60-question HotpotQA slice."

### 4. (Optional but worth it) Run the ablation

Read `04_ablation_patch.md` carefully, it walks you through a small
code change to `retrieve_service.py` that lets you toggle the graph
and vector branches off independently, then re-run steps 2 and 3 twice
more (vector-only, graph-only).

### 5. Compare all three and get your final chart

```bash
python 05_compare_ablation.py \
    --hybrid ragas_hybrid.json \
    --vector_only ragas_vector_only.json \
    --graph_only ragas_graph_only.json
```

This prints the full comparison table and saves a bar chart
(`ablation_comparison.png`) you can literally drop into a README or a
resume portfolio page. This is the number that actually proves your
hybrid design choice was worth it, not just "I ran an eval."

## What "good" looks like

There's no universal passing score, but as a sanity check:
- **Faithfulness above 0.8** means the model is mostly not hallucinating
  beyond its retrieved context
- **Context recall meaningfully higher in Hybrid than Vector-only on
  multi_hop and comparison categories specifically** is the result
  that validates the whole point of building the graph layer
- If Hybrid and Vector-only score about the same everywhere, that's
  still a useful, honest finding, it means the graph layer isn't
  earning its complexity on this particular question set, and is
  worth reporting as-is rather than hidden

## Troubleshooting

- **Empty contexts in results.json**: check `extract_fields()` in
  `02_run_queries.py` against the real response schema at
  `localhost:8000/docs`
- **RAGAS scores all near 0**: usually means the judge LLM (qwen2.5:7b)
  is struggling with the scoring prompt format, try re-running just a
  few questions first with `--n 5` in step 1 to sanity check before
  committing to a full 60-question run
- **Ingestion seems stuck**: check both watcher terminals for errors,
  Neo4j vec# Hybrid RAG Evaluation Toolkit

Evaluates the agentic-graph-rag pipeline on a real benchmark (HotpotQA)
using RAGAS metrics, with a hybrid vs vector-only vs graph-only ablation.

## Before you start

Your pipeline must already be fully running:
- Neo4j up (`docker ps` shows it)
- Ollama running with `qwen2.5:7b` and `mxbai-embed-large` pulled
- Both ingestion watchers running
- Backend running on `localhost:8000`
- (Chainlit frontend is optional for this, we talk to the backend API directly)

## Setup

```bash
cd hybrid_rag_eval
pip install -r requirements-eval.txt --break-system-packages
```

## Step by step

### 1. Download the benchmark and build your test corpus

```bash
python 01_download_hotpotqa.py --n 60 --out_dir ../agentic-graph-rag/knowledge --questions_out questions.json
```

This drops ~60 questions worth of Wikipedia paragraphs straight into
your repo's `knowledge/` folder. Your two watcher terminals should
start printing ingestion activity within a few seconds, since Docker/
Ollama/watchers are already running from earlier.

**Wait for ingestion to finish** before moving on. With ~60 questions
you'll get somewhere around 150-250 unique context files (HotpotQA
gives 10 paragraphs per question, several overlap). Give it a few
minutes, check your watcher terminals stop printing new activity.

### 2. Run every question through your live pipeline

```bash
python 02_run_queries.py --questions questions.json --out results.json
```

This pauses after question 1 and shows you the raw API response, so
you can confirm the script is reading the right fields (`answer`,
`context`) before it runs through all 60. If the extracted answer/
context look wrong, open `02_run_queries.py`, find `extract_fields()`,
and match the key names to what you see printed.

This takes a while, local LLM inference on ~60 questions with a retry
loop that can run up to 7 iterations per question is not fast. Let it run.

### 3. Score with RAGAS

```bash
python 03_evaluate_ragas.py --results results.json --out ragas_scores.json
```

Prints overall scores and a breakdown by category (single_hop,
multi_hop, comparison) straight to your terminal, and saves the full
per-question scores to `ragas_scores.json`.

This is a real, reportable result on its own: something like
"faithfulness 0.82, context recall 0.71 on a 60-question HotpotQA slice."

### 4. (Optional but worth it) Run the ablation

Read `04_ablation_patch.md` carefully, it walks you through a small
code change to `retrieve_service.py` that lets you toggle the graph
and vector branches off independently, then re-run steps 2 and 3 twice
more (vector-only, graph-only).

### 5. Compare all three and get your final chart

```bash
python 05_compare_ablation.py \
    --hybrid ragas_hybrid.json \
    --vector_only ragas_vector_only.json \
    --graph_only ragas_graph_only.json
```

This prints the full comparison table and saves a bar chart
(`ablation_comparison.png`) you can literally drop into a README or a
resume portfolio page. This is the number that actually proves your
hybrid design choice was worth it, not just "I ran an eval."

## What "good" looks like

There's no universal passing score, but as a sanity check:
- **Faithfulness above 0.8** means the model is mostly not hallucinating
  beyond its retrieved context
- **Context recall meaningfully higher in Hybrid than Vector-only on
  multi_hop and comparison categories specifically** is the result
  that validates the whole point of building the graph layer
- If Hybrid and Vector-only score about the same everywhere, that's
  still a useful, honest finding, it means the graph layer isn't
  earning its complexity on this particular question set, and is
  worth reporting as-is rather than hidden

## Troubleshooting

- **Empty contexts in results.json**: check `extract_fields()` in
  `02_run_queries.py` against the real response schema at
  `localhost:8000/docs`
- **RAGAS scores all near 0**: usually means the judge LLM (qwen2.5:7b)
  is struggling with the scoring prompt format, try re-running just a
  few questions first with `--n 5` in step 1 to sanity check before
  committing to a full 60-question run
- **Ingestion seems stuck**: check both watcher terminals for errors,
  Neo4j vector indexing in particular can silently fail if
  `index_documents_to_neo4j()` isn't being called, per the repo's own
  engineering notestor indexing in particular can silently fail if
  `index_documents_to_neo4j()` isn't being called, per the repo's own
  engineering notes