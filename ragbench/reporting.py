"""Render a portable HTML review and a measured Markdown case study."""
import json
from pathlib import Path


def pct(value):
    return "not defined" if value is None else f"{value:.1%}"


def create_reports(root, report):
    root = Path(root)
    methods = report["methods"]
    lines = ["# Retrieval evaluation prototype: measured case study", "",
      f"**Azaz Butt | Independent portfolio demonstration | Original fixture: 30 October 2026 | Revalidated: {report['created_at_utc'][:10]} UTC**", "",
      "## Problem and scope", "",
      "A fictional B2B support assistant must find the appropriate policy passage, cite it and abstain when its eligible knowledge base cannot support an answer. This sample demonstrates how a narrowly scoped evaluation engagement can produce runnable code, reproducible comparisons and actionable failure analysis.", "",
      "The delivered pipeline runs BM25, lexical hybrid retrieval (BM25 plus character-trigram TF-IDF with reciprocal-rank fusion), and the same hybrid followed by a transparent feature reranker. The reranker is not a neural cross-encoder, and the hybrid does not use dense embeddings. All methods use identical current/public/plan eligibility filters.", "",
      "Answers are complete verbatim source excerpts. No LLM or external API was used. This enables citation and abstention inspection without a model key, but does not demonstrate a deployed generative application.", "",
      "## Evaluation protocol", "",
      "The original synthetic fixture has 48 passages and 96 questions. There are 48 development and 48 test questions, each containing 36 answerable and 12 unanswerable cases. Question intent groups do not cross splits. The fixed source corpus is available to every retriever. All weights and the domain lexicon were written before the first benchmark run. Each method's abstention threshold is selected only on development cases using the published utility, then frozen for the reported test run. The author created both the data and implementation; this is not an independently annotated benchmark.", "",
      "## Observed test results", "",
      "| Method | Recall@1 | Recall@5 | MRR@5 | nDCG@5 | Answer coverage* | Incorrect answers on negatives |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, summary in methods.items():
        lines.append(f"| {name} | {pct(summary['recall_at_1'])} | {pct(summary['recall_at_5'])} | {summary['mrr_at_5']:.3f} | {summary['ndcg_at_5']:.3f} | {pct(summary['answer_coverage_answerable'])} | {pct(summary['false_answer_rate_unanswerable'])} |")
    lines += ["", "*Coverage uses the 36 answerable cases. Retrieval metrics exclude unanswerable cases. Incorrect-answer rate uses the 12 unanswerable cases. These denominators are deliberately separate.", "",
      "Sparse hybrid achieved the highest MRR point estimate in this run. The feature reranker reduced overall MRR compared with hybrid alone; the implementation and test set were not retuned to remove that result. Hybrid also uses vocabulary expansion, so its difference from raw-query BM25 cannot be attributed to character retrieval alone.", "",
      "An answered case passes the automated correctness proxy only when it cites a relevant eligible source and contains the expected answer substring. This proxy can over-credit an incomplete or ambiguous excerpt. Verbatim quote integrity measures copying from a source, not semantic faithfulness. No hallucination-reduction claim is made.", "",
      "## Uncertainty and failures", ""]
    for name, summary in methods.items():
        interval = summary['cluster_bootstrap_95_ci']['mrr_at_5']
        lines.append(f"- {name}: MRR@5 95% intent-cluster bootstrap interval {interval[0]:.3f} to {interval[1]:.3f}; failure counts {json.dumps(summary['failure_counts'], sort_keys=True)}.")
    paired = report["paired_reranked_minus_bm25_mrr"]
    lines += ["", f"The paired reranked-minus-BM25 MRR difference is {paired['difference']:+.3f}, with a 95% intent-cluster bootstrap interval from {paired['cluster_bootstrap_95_ci'][0]:+.3f} to {paired['cluster_bootstrap_95_ci'][1]:+.3f}. The interval reflects this small authored fixture only and is not a population guarantee.", "",
      "Every failed case is exported in reports/failures.csv and inspectable in the HTML report. A conservative gate can reduce incorrect answers while rejecting useful answers; assess that trade-off alongside coverage. Do not hide abstained answerable questions.", "",
      "## Engineering checks", ""]
    for key, passed in report["engineering_checks"].items():
        lines.append(f"- {key}: {'PASS' if passed else 'FAIL'}")
    lines += ["", "Passing these checks does not establish production security, semantic answer quality, regulatory compliance or suitability for a real client.", "",
      "## Practical next experiment", "",
      "Collect and independently label a representative client query set, including confusing policies, multi-document questions and unknown answers. Freeze it before tuning. Compare BM25, a genuine embedding retriever and a neural cross-encoder under identical filters. Evaluate actual generator outputs with human review of citation support, completeness and unsupported claims. Load testing, authentication, corpus chunking, version handling and monitoring are separate production work.", "",
      "## What this sample supports", "",
      "It supports a truthful statement that Azaz has a runnable offline retrieval-evaluation prototype with baseline comparisons, development-only threshold calibration, failure analysis, eligibility tests and documented handover. It does not establish previous paid client work, a shipped production RAG system or the performance of dense/neural retrieval.", ""]
    (root / "docs/CASE_STUDY.md").write_text("\n".join(lines), encoding="utf-8")
    template = (root / "web/index.html").read_text(encoding="utf-8")
    payload = json.dumps(report, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    standalone = template.replace("<!-- REPORT_DATA -->", "<script>window.REPORT_DATA=" + payload + ";</script>")
    (root / "reports/index.html").write_text(standalone, encoding="utf-8")

