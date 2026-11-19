# Retrieval evaluation prototype: measured case study

**Azaz Butt | Independent portfolio demonstration | Original fixture: 30 October 2026 | Revalidated: 2026-11-02 UTC**

## Problem and scope

A fictional B2B support assistant must find the appropriate policy passage, cite it and abstain when its eligible knowledge base cannot support an answer. This sample demonstrates how a narrowly scoped evaluation engagement can produce runnable code, reproducible comparisons and actionable failure analysis.

The delivered pipeline runs BM25, lexical hybrid retrieval (BM25 plus character-trigram TF-IDF with reciprocal-rank fusion), and the same hybrid followed by a transparent feature reranker. The reranker is not a neural cross-encoder, and the hybrid does not use dense embeddings. All methods use identical current/public/plan eligibility filters.

Answers are complete verbatim source excerpts. No LLM or external API was used. This enables citation and abstention inspection without a model key, but does not demonstrate a deployed generative application.

## Evaluation protocol

The original synthetic fixture has 48 passages and 96 questions. There are 48 development and 48 test questions, each containing 36 answerable and 12 unanswerable cases. Question intent groups do not cross splits. The fixed source corpus is available to every retriever. All weights and the domain lexicon were written before the first benchmark run. Each method's abstention threshold is selected only on development cases using the published utility, then frozen for the reported test run. The author created both the data and implementation; this is not an independently annotated benchmark.

## Observed test results

| Method | Recall@1 | Recall@5 | MRR@5 | nDCG@5 | Answer coverage* | Incorrect answers on negatives |
|---|---:|---:|---:|---:|---:|---:|
| bm25 | 77.8% | 91.7% | 0.831 | 0.853 | 41.7% | 0.0% |
| hybrid | 86.1% | 94.4% | 0.903 | 0.914 | 80.6% | 0.0% |
| reranked | 83.3% | 94.4% | 0.889 | 0.903 | 80.6% | 0.0% |

*Coverage uses the 36 answerable cases. Retrieval metrics exclude unanswerable cases. Incorrect-answer rate uses the 12 unanswerable cases. These denominators are deliberately separate.

Sparse hybrid achieved the highest MRR point estimate in this run. The feature reranker reduced overall MRR compared with hybrid alone; the implementation and test set were not retuned to remove that result. Hybrid also uses vocabulary expansion, so its difference from raw-query BM25 cannot be attributed to character retrieval alone.

An answered case passes the automated correctness proxy only when it cites a relevant eligible source and contains the expected answer substring. This proxy can over-credit an incomplete or ambiguous excerpt. Verbatim quote integrity measures copying from a source, not semantic faithfulness. No hallucination-reduction claim is made.

## Uncertainty and failures

- bm25: MRR@5 95% intent-cluster bootstrap interval 0.713 to 0.949; failure counts {"abstained_answerable": 21}.
- hybrid: MRR@5 95% intent-cluster bootstrap interval 0.833 to 0.972; failure counts {"abstained_answerable": 7, "wrong_source_or_span": 3}.
- reranked: MRR@5 95% intent-cluster bootstrap interval 0.819 to 0.958; failure counts {"abstained_answerable": 7, "wrong_source_or_span": 3}.

The paired reranked-minus-BM25 MRR difference is +0.058, with a 95% intent-cluster bootstrap interval from -0.032 to +0.162. The interval reflects this small authored fixture only and is not a population guarantee.

Every failed case is exported in reports/failures.csv and inspectable in the HTML report. A conservative gate can reduce incorrect answers while rejecting useful answers; assess that trade-off alongside coverage. Do not hide abstained answerable questions.

## Engineering checks

- valid_schema_and_disjoint_intent_groups: PASS
- eligibility_controls_27_of_27: PASS
- no_restricted_or_archived_ranked_hits: PASS
- answered_text_is_verbatim_source: PASS

Passing these checks does not establish production security, semantic answer quality, regulatory compliance or suitability for a real client.

## Practical next experiment

Collect and independently label a representative client query set, including confusing policies, multi-document questions and unknown answers. Freeze it before tuning. Compare BM25, a genuine embedding retriever and a neural cross-encoder under identical filters. Evaluate actual generator outputs with human review of citation support, completeness and unsupported claims. Load testing, authentication, corpus chunking, version handling and monitoring are separate production work.

## What this sample supports

It supports a truthful statement that Azaz has a runnable offline retrieval-evaluation prototype with baseline comparisons, development-only threshold calibration, failure analysis, eligibility tests and documented handover. It does not establish previous paid client work, a shipped production RAG system or the performance of dense/neural retrieval.
