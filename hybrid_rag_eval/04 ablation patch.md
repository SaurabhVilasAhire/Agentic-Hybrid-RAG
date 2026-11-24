# Ablation setup (hybrid vs vector-only vs graph-only)

Your repo does not ship a built-in toggle to disable one retrieval branch,
so this is a small manual patch you add yourself, run the eval, then
revert. Do this AFTER you've already run steps 01-03 once with the
normal hybrid pipeline, that first run is your "hybrid" baseline.

## Where to patch

Open `backend/services/retrieve_service.py`. Find the method that runs
both the graph branch and the vector branch (per the repo's own docs,
this is the `Hybrid Retriever` node, look for where it calls both the
Neo4j Cypher entity traversal AND the Neo4j vector / FAISS search, then
merges results before reranking).

Add an environment-variable-controlled skip at the top of each branch:

```python
import os

DISABLE_GRAPH = os.getenv("EVAL_DISABLE_GRAPH", "false").lower() == "true"
DISABLE_VECTOR = os.getenv("EVAL_DISABLE_VECTOR", "false").lower() == "true"

# inside the retrieval method, before the graph branch runs:
if not DISABLE_GRAPH:
    graph_results = self._run_graph_retrieval(query)
else:
    graph_results = []

# before the vector branch runs:
if not DISABLE_VECTOR:
    vector_results = self._run_vector_retrieval(query)
else:
    vector_results = []
```

(Exact method/variable names will differ slightly, match this pattern
to whatever the real method is called in your copy of the file.)

## Running the three ablation passes

**Pass 1: Hybrid (already done in steps 01-03)**
```
python 02_run_queries.py --out results_hybrid.json
python 03_evaluate_ragas.py --results results_hybrid.json --out ragas_hybrid.json
```

**Pass 2: Vector-only**
```
# Windows PowerShell:
$env:EVAL_DISABLE_GRAPH="true"
# restart your backend (uvicorn) so it picks up the new env var
python 02_run_queries.py --out results_vector_only.json
python 03_evaluate_ragas.py --results results_vector_only.json --out ragas_vector_only.json
```

**Pass 3: Graph-only**
```
$env:EVAL_DISABLE_GRAPH="false"
$env:EVAL_DISABLE_VECTOR="true"
# restart your backend again
python 02_run_queries.py --out results_graph_only.json
python 03_evaluate_ragas.py --results results_graph_only.json --out ragas_graph_only.json
```

Restarting the backend between passes matters, since the env vars are
read once at import time in the patch above.

Once you have all three `ragas_*.json` files, run `05_compare_ablation.py`
to generate the final comparison table and chart.