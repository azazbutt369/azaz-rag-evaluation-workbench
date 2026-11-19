# RAG Evaluation Workbench

**Azaz Butt | Independent portfolio prototype | v1.1**

This sample supports a scoped **RAG Evaluation & Regression Audit**. Read
`docs/CLIENT_BRIEF.pdf` for the client overview, `docs/ARCHITECTURE.md` for the
implementation, and `docs/EVALUATION_CRITERIA.md` for the test protocol and
commercial acceptance boundaries. Measured example outputs are in
`docs/SAMPLE_OUTPUTS.md` and `reports/sample_outputs.json`. The original fixture
and ranking/evaluation methods remain frozen; see `docs/RELEASE_NOTES.md`.

A working evaluation sample for a fictional B2B support knowledge base. It
compares retrieval methods, produces cited source excerpts or abstentions,
exports every failed answer-gate case and serves a local inspection interface.
Python 3.10+ is the only runtime requirement. No package installation, GPU,
model download, API key or paid service is required for the included demo.

## Start in two minutes

Extract the ZIP, open a terminal in this project directory, then run:

```bash
python -m unittest discover -s tests -v
python -m ragbench validate
python -m ragbench benchmark --output reports/recheck --check
python scripts/check_regression.py reports/benchmark.json reports/recheck/benchmark.json
python scripts/build_review_assets.py
python -m ragbench serve
```

Open **http://127.0.0.1:8765**. Stop the server with Ctrl+C.
On macOS/Linux, use `python3` if `python` is unavailable. On Windows, `py -3`
can be used instead. For a review without running Python, open
`reports/index.html` directly in a browser. That report contains measured
benchmark results and interactive case inspection; arbitrary new questions
require the local server.

The committed report is the reference evidence. The quickstart writes a fresh
run to `reports/recheck` and compares it without overwriting that reference.

## What to demonstrate to a prospect

1. Show the BM25, sparse hybrid and feature-reranked comparison.
2. Open a paraphrased question and inspect the gold source and returned order.
3. Inspect an unanswerable question and at least one failure. Explain coverage
   alongside incorrect answers, rather than quoting a single attractive score.
4. Run a fresh query in the local demo and inspect its source excerpt.
5. Show the JSON/CSV evidence, test suite and client-pilot scope.

Suggested fresh questions:

```bash
python -m ragbench query "How do I rotate an API key without interrupting integrations?"
python -m ragbench query "What will an Enterprise subscription cost in 2031?"
python -m ragbench query "Which endpoint checks an ingestion job?" --method bm25
```

Do not promise that every unknown question abstains. The included false-answer
and false-abstention reports show the actual behaviour of the heuristic gate.

## Exact scope

| Component | Implemented and measured |
|---|---|
| Baseline | BM25, k1=1.5 and b=0.75, title plus body |
| Hybrid | BM25 + character-trigram TF-IDF, reciprocal-rank fusion, constant 60 |
| Reranker | Transparent weighted lexical features over the top 12 hybrid candidates |
| Eligibility | Identical current/public/plan filtering before every method |
| Answer mode | Complete verbatim excerpt of the top source, or abstention |
| Gate | Heuristic overlap/similarity score, development-only threshold selection |
| Metrics | Recall@1/5, MRR@5, nDCG@5, coverage, negative-case false answers, source/span proxy |
| Uncertainty | Intent-cluster bootstrap, 1,000 samples, fixed seed |
| Evidence | Per-query results, failure CSV, data and run hashes, measured case study |
| Interface | Local Python API and dashboard; portable interactive HTML report |
| External outputs | Strict JSONL contract for checking client-supplied generated responses |

The hybrid is **not dense retrieval**. The reranker is **not a neural
cross-encoder**. No generative model was run, and no real client's production
system was evaluated. The sample is an independent demonstration, not a
customer case study. See `data/DATA_CARD.md` and `docs/CASE_STUDY.md` for limits.

Hybrid and reranked methods also use the explicit domain vocabulary in
`data/lexicon.json`; BM25 uses the raw question. Their difference from BM25
therefore combines query expansion and fusion. It does not isolate the benefit
of either one. Reranked versus hybrid isolates the added feature reranking.

On the included test run, sparse hybrid has the highest MRR point estimate.
Adding the feature reranker slightly reduces overall MRR. The paired
reranked-minus-BM25 interval includes zero. These observations are retained,
without tuning the method on the test set to produce a better headline.

## Protocol

The original fictional fixture contains 48 passages and 96 questions across 36
intent groups. Development and test each have 36 answerable and 12 unanswerable
questions. Paraphrases of the same intent never cross splits. Source documents
are shared across splits because the task is fixed-corpus retrieval.

The domain lexicon and ranking weights were written before the first benchmark
execution. The same author created the questions and implementation, so this is
not a blind independent test. The manifest records the frozen fixture and code.
Abstention thresholds are selected using development cases only, with utility:

```text
correct answers - 4 * incorrect answers - 0.5 * abstained answerable questions
```

Each method uses a threshold from the fixed grid 0.00, 0.05, ..., 1.00. Ties choose
the higher threshold. The resulting thresholds are frozen for test evaluation.
The test split must not be used to choose a better lexicon, ranking weight or
threshold. If you intentionally change the method after seeing test results,
label that set development data and create a fresh test set.

Retrieval metrics use answerable questions only. False-answer rate uses
unanswerable questions only. Answer correctness is a **source-and-substring
proxy**, not semantic faithfulness. The complete source excerpt may contain
the answer while failing to address the exact question. Verbatim quote integrity
is a construction check and cannot substantiate a hallucination-free claim.

All retrieval algorithms see the same eligible candidates. Archived and internal
passages are included as control fixtures but cannot be returned. Plan selection
simulates public entitlement context; it is not a replacement for authenticated
tenant authorisation in a deployed system.

## Project map

```text
ragbench/       retrieval, evaluation, reporting, API and CLI
data/           corpus, questions, domain vocabulary, data card and frozen manifest
tests/          standard-library unittest suite
web/            live local interface template
reports/        measured JSON, failure CSV, manifest and portable HTML
docs/           case study, demo script, pilot scope, API and portfolio gap plan
```

## Use your own evaluation data

Make a copy of the project, replace the JSONL files and domain lexicon, validate,
and rerun. Do not overwrite the reference fixture and keep its results attached
to the old data.

`data/corpus.jsonl`, one object per passage:

```json
{"id":"policy-1","title":"Refund policy","text":"Refunds are available within 14 days.","topic":"refunds","status":"current","visibility":"public","plans":["starter","growth","enterprise"]}
```

`data/queries.jsonl`, one object per evaluation question:

```json
{"id":"q1","question":"How long can I request a refund?","group":"refund-window","split":"dev","plan":"growth","relevant_ids":["policy-1"],"answer_phrase":"14 days","category":"direct"}
```

Unanswerable queries have `relevant_ids: []` and `answer_phrase: ""`.
Both splits need answerable and unanswerable cases. Use separate intent groups
for development and test. `plans` accepts `starter`, `growth`, `enterprise`;
`status` accepts `current`, `archived`; `visibility` accepts `public`, `internal`.
The demonstration vocabulary can be replaced for another domain. Chunk real
documents upstream and use stable passage IDs. This prototype does not ingest
PDF files, run OCR or automatically create trustworthy relevance labels.

## Check actual model responses

The workbench can check responses produced by an external system. It does not
send data to a provider or call a model itself. Supply one record for every
question in the selected split:

```json
{"id":"test-api-rotation-1","answer":"First create a second key, then update integrations.","citation_ids":["api-rotation"],"abstained":false}
```

```bash
python -m ragbench score-responses my_predictions.jsonl --split test
```

The checker flags invalid/ineligible source IDs and checks expected answer
substrings plus relevant citations. Missing, extra and duplicate predictions
are errors. It deliberately does **not** label fluent generated answers as
semantically grounded. Human or separately validated semantic review is needed
for added unsupported claims, omissions and contradictory statements.

A complete runnable contract example is supplied in
`examples/demo_extractive_responses.jsonl`. It contains the actual extractive
hybrid test responses, not LLM outputs:

```bash
python -m ragbench score-responses examples/demo_extractive_responses.jsonl --split test
```

## Reproducibility and regression

```bash
python -m ragbench benchmark --output reports/recheck --check
python scripts/check_regression.py reports/benchmark.json reports/recheck/benchmark.json
```

The regression comparison checks data fingerprints, selected thresholds,
quality metrics and per-case rankings, answers, citations and decisions against
the committed reference. Timing and timestamps are
excluded because they vary by run and hardware. CI runs the same comparison.
Engineering checks do not assert a commercial quality target; acceptance criteria
must be agreed for a real use case. The test suite includes metric arithmetic,
split contamination, source eligibility, source-quote integrity, invalid API
inputs and external-response validation.

## Local API

```bash
curl -X POST http://127.0.0.1:8765/api/search -H "Content-Type: application/json" -d '{"question":"How long are audit events retained?","method":"reranked","plan":"growth"}'
```

The server binds only to loopback. It has no authentication or production
deployment claim. It rejects caller-supplied role/visibility fields and serves
public eligible sources only. It does not execute tools or source instructions.
See `docs/API.md` for the complete local contract and deployment boundaries.

## References

- [BEIR evaluation framework](https://github.com/beir-cellar/beir): independent
  reference for common retrieval metrics and evaluation structure. No BEIR data
  or performance result is included or claimed here.
- [scikit-learn model-evaluation documentation](https://scikit-learn.org/stable/modules/model_evaluation.html):
  reference for matching metrics to the decision problem. The implementation
  here uses Python's standard library, not scikit-learn.

Code and synthetic data are supplied under the included MIT licence.
Run this release from its extracted source directory. Building and installing
a standalone wheel with bundled data is outside this release's packaging scope.

