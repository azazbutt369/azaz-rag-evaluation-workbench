# Five-minute demonstration

## 0:00 to 0:40: Set the scope

"This is an independent prototype on a fictional support knowledge base. It
shows how I structure an evaluation engagement: compare retrieval baselines,
inspect failures and hand over a suite an engineering team can rerun. The answer
mode here quotes source passages. I am not presenting it as a client deployment."

## 0:40 to 1:40: Explain the comparison

Open `reports/index.html`. Describe BM25, lexical hybrid and the transparent
feature reranker. Point out that every method uses the same eligible source set.
Show Recall@5 together with MRR, coverage and incorrect answers on negative cases.
Use the actual numbers visible in the report. Do not promise that reranking always
improves every metric.

## 1:40 to 2:40: Inspect evidence

Open Inspect questions. Select a direct question and a paraphrase. Compare methods.
Read the returned source ID, gold source and answer excerpt. Explain why a source
containing the expected substring may still need human review for completeness.

## 2:40 to 3:40: Show a failure

Choose Answer-gate failures. Explain one false abstention or unsupported answer.
Then inspect a restricted-source or missing-fact question. The access filters are
deterministic prototype controls; production tenant authorisation requires a
separate implementation and review.

## 3:40 to 4:30: Demonstrate reproducibility

Run `python -m unittest discover -s tests -v` and show `reports/failures.csv`.
Explain that threshold calibration uses development cases and the test questions
are grouped by intent. No results are guaranteed on real customer questions.

## 4:30 to 5:00: Connect to a paid pilot

"For your system, I would start with one workflow, agree an evaluation set and
acceptance criteria, then deliver the benchmark, annotated failures and an
engineering handover. We would decide whether retrieval, generation or source
quality is the main constraint before expanding scope."

