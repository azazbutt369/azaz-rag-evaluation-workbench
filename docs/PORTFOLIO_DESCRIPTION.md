# Portfolio description

## Short version

Built a reproducible RAG evaluation workbench for a fictional B2B support knowledge base. It compares BM25, sparse hybrid retrieval and feature reranking, with development-only abstention calibration, grouped test queries, citation checks and per-case regression detection. Includes runnable Python code, an inspection dashboard, failure analysis and handover guidance. Independent synthetic demonstration; no client deployment or live LLM inference is claimed.

## Version with measured results

On an authored test fixture with 36 answerable and 12 unanswerable questions, sparse hybrid retrieved the relevant source in the top five for 34/36 answerable queries, versus 33/36 for BM25. Its MRR@5 was 0.903 versus 0.831. The report retains three unsuitable source answers and seven false abstentions, and shows that feature reranking reduced MRR to 0.889. Results demonstrate an evaluation workflow on synthetic data, not customer performance.

## Service attached to the sample

RAG Evaluation & Regression Audit: scope one workflow, agree the evaluation set, compare a baseline with one candidate, inspect retrieval and answer failures, and hand over reproducible checks and a prioritised improvement plan. Scope, timing, price and commercial acceptance criteria are agreed after inspecting the client's system.
