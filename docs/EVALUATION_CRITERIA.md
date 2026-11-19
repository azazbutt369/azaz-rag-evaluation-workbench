# Evaluation criteria and acceptance

## Included sample: implemented checks

| Question | Metric / criterion | Denominator and interpretation |
|---|---|---|
| Is relevant evidence retrieved? | Recall@1 and Recall@5 | Macro mean over 36 answerable test queries. Each fixture query has one relevant source; 34/36 hybrid queries find it in the top five |
| How early is the relevant passage? | MRR@5 and nDCG@5 | Answerable queries only. Reciprocal rank is zero beyond rank five; binary relevance is used |
| How often does the gate answer? | Answer coverage | Answered / 36 answerable queries. Hybrid answers 29/36 |
| Are answered cases useful under the proxy? | Relevant eligible source + expected substring | Hybrid passes 26/36 answerable cases, or 26/29 issued answers. This is not semantic correctness |
| Are unknown answers rejected? | False-answer rate on negatives | Answered / 12 unanswerable queries. Hybrid: 0/12; this small authored set does not establish a zero population failure rate |
| Can errors be inspected? | Complete per-case outputs and failure export | All 48 test cases per method in JSON/HTML; all gate failures in CSV |
| Are protected fixture sources excluded? | Zero ineligible ranked hits; 27 additional eligibility combinations pass | Prototype metadata controls only. No production tenant-security or injection-defence claim |
| Is the split contaminated? | Zero repeated query text; zero intent groups across dev/test; valid eligible gold spans | Schema and declared-group checks. Undeclared semantic overlap, pretraining contamination and real training-data leakage are not established |
| Does a rerun reproduce? | Same hashes, thresholds, aggregate quality and per-case behaviour | Exact reproduction gate; timestamps and latency excluded. Changes require review rather than automatic acceptance |
| Is the original experiment preserved? | All five frozen fixture/vocabulary/method hashes match | Corpus, questions, lexicon, retrieval.py and evaluation.py remain unchanged from the original freeze |

Uncertainty uses 1,000 fixed-seed bootstrap samples drawn by intent group. This accounts for grouped paraphrases within this small authored fixture; it does not make the sample representative of a customer's traffic. The BM25-to-hybrid comparison changes both query expansion and fusion, so it does not isolate one algorithmic contribution.

## Visible failure analysis

Hybrid returns a source excerpt for 29 answerable cases: 26 pass the source/span proxy and three cite an unsuitable top source. Seven answerable questions are rejected. All 12 negative cases abstain. The wrong answers and false abstentions remain in the deliverable.

For `test-roles-2`, the correct roles passage appears at rank two, but the gate accepts an irrelevant failed-payment passage at rank one. This is a ranking/answer-selection problem. For `test-api-rotation-3`, the right passage is rank one, but its support score 0.329479 is below threshold 0.35. This is a gate false abstention. These cases show why top-five recall alone is insufficient.

The feature reranker reduces test MRR from 0.903 to 0.889. Retain the simpler hybrid as the next candidate for independent validation; do not promote a more complex method solely because it adds a reranking stage.

## Proposed paid pilot: criteria to agree

This is a proposed contract shape, not an agreed delivery promise. Agree one workflow, a permitted source snapshot, independently reviewed relevance labels, development/test groups and a baseline. Set a minimum retrieval quality, useful coverage and maximum unsupported-answer rate after observing that baseline. Record critical safety cases separately from average metrics. Establish acceptable p95 end-to-end latency on the client's environment and account for token/API cost if a live generator is in scope.

Every supported-answer review should check source support for each material claim, completeness, contradiction and appropriate abstention. Two reviewers with a documented adjudication process are a useful option where error cost warrants it. The exact reproduction gate supplied here catches code/data drift; it is not a statistical model-release approval policy. A client comparison needs an agreed non-inferiority margin and risk-based acceptance rules.
