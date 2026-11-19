"""Development-only calibration, intent-cluster bootstrap, and failure analysis."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics

from . import __version__
from .io import fingerprint, read_jsonl, validate, write_json
from .retrieval import SearchIndex

METHODS = ("bm25", "hybrid", "reranked")


def ranking_metrics(ranked, relevant, k=5):
    if not relevant:
        return None
    relevant = set(relevant)
    # Deduplicate IDs so duplicated returned passages cannot inflate recall.
    ranked = list(dict.fromkeys(ranked))[:k]
    hits = [1 if x in relevant else 0 for x in ranked]
    dcg = sum(h / math.log2(i + 2) for i, h in enumerate(hits))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return {"recall_at_1": float(bool(hits and hits[0])) / len(relevant),
            "recall_at_5": sum(hits) / len(relevant),
            "mrr_at_5": next((1 / (i + 1) for i, h in enumerate(hits) if h), 0.0),
            "ndcg_at_5": dcg / ideal if ideal else 0.0}


def quantile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    location = fraction * (len(values) - 1)
    low, high = math.floor(location), math.ceil(location)
    return values[low] + (values[high] - values[low]) * (location - low)


def mean(values):
    values = list(values)
    return statistics.mean(values) if values else None


def cluster_interval(rows, field, samples=1000):
    groups = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row[field])
    keys = sorted(groups)
    if not keys:
        return None
    rng = random.Random(20261030)
    means = []
    for _ in range(samples):
        drawn = rng.choices(keys, k=len(keys))
        means.append(mean(x for key in drawn for x in groups[key]))
    return [quantile(means, .025), quantile(means, .975)]


def calibration_threshold(index, dev, method):
    observations = []
    for query in dev:
        result = index.answer(query["question"], method, query["plan"], threshold=0)
        top = result["hits"][0] if result["hits"] else None
        score = top["support_score"] if top and top["score"] > 0 else -1
        valid = bool(top and top["id"] in query["relevant_ids"] and
                     query["answer_phrase"].casefold() in top["text"].casefold())
        observations.append((score, valid, bool(query["relevant_ids"])))
    candidates = []
    # Fixed grid and utility declared before test execution.
    for integer in range(21):
        threshold = integer / 20
        counts = Counter()
        for score, valid, answerable in observations:
            if score >= threshold:
                counts["correct_answers" if valid else "incorrect_answers"] += 1
            elif answerable:
                counts["abstained_answerable"] += 1
        utility = counts["correct_answers"] - 4 * counts["incorrect_answers"] - .5 * counts["abstained_answerable"]
        candidates.append({"threshold": threshold, "utility": utility, **dict(counts)})
    selected = max(candidates, key=lambda x: (x["utility"], x["threshold"]))
    return selected["threshold"], {"selected": selected, "grid": candidates,
        "selection_split": "dev", "utility": "correct_answers - 4*incorrect_answers - 0.5*abstained_answerable"}


def evaluate_method(index, questions, method, threshold):
    rows = []
    for query in questions:
        response = index.answer(query["question"], method, query["plan"], threshold)
        ordered = [h["id"] for h in response["hits"]]
        metrics = ranking_metrics(ordered, query["relevant_ids"])
        answered = not response["abstained"]
        correct = bool(answered and response["citation"]["id"] in query["relevant_ids"] and
                       query["answer_phrase"].casefold() in response["answer"].casefold())
        quote_integrity = (not answered or response["answer"] == index.documents[response["citation"]["id"]]["text"])
        violation = any(key not in index.eligible_ids(query["plan"]) for key in ordered)
        answerable = bool(query["relevant_ids"])
        failure = ("false_answer_unanswerable" if answered and not answerable else
                   "wrong_source_or_span" if answered and not correct else
                   "abstained_answerable" if not answered and answerable else "")
        rows.append({"id": query["id"], "group": query["group"], "category": query["category"],
            "question": query["question"], "plan": query["plan"], "answerable": answerable,
            "relevant_ids": query["relevant_ids"], "answer_phrase": query["answer_phrase"],
            "ranked_ids": ordered, "answer": response["answer"], "citation": response["citation"],
            "support_score": response["hits"][0]["support_score"] if response["hits"] else 0,
            "abstained": response["abstained"], "correct_answer_proxy": correct,
            "quote_integrity": quote_integrity, "eligibility_violation": violation,
            "latency_ms": response["latency_ms"], "failure": failure, **(metrics or {})})
    return rows


def summarise(rows):
    positive = [r for r in rows if r["answerable"]]
    negative = [r for r in rows if not r["answerable"]]
    answered = [r for r in rows if not r["abstained"]]
    summary = {field: mean(r[field] for r in positive) for field in
               ("recall_at_1", "recall_at_5", "mrr_at_5", "ndcg_at_5")}
    summary.update({"answerable_count": len(positive), "unanswerable_count": len(negative),
        "answer_coverage_answerable": mean(not r["abstained"] for r in positive),
        "correct_answer_rate_answerable": mean(r["correct_answer_proxy"] for r in positive),
        "false_answer_rate_unanswerable": mean(not r["abstained"] for r in negative),
        "correct_abstention_rate_unanswerable": mean(r["abstained"] for r in negative),
        "selective_answer_accuracy_proxy": mean(r["correct_answer_proxy"] for r in answered),
        "answered_count": len(answered),
        "verbatim_quote_integrity_answered": mean(r["quote_integrity"] for r in answered),
        "eligibility_violations": sum(r["eligibility_violation"] for r in rows),
        "latency_ms_p50": quantile([r["latency_ms"] for r in rows], .5),
        "latency_ms_p95": quantile([r["latency_ms"] for r in rows], .95),
        "failure_counts": dict(Counter(r["failure"] for r in rows if r["failure"]))})
    summary["cluster_bootstrap_95_ci"] = {field: cluster_interval(positive, field) for field in
                                               ("recall_at_1", "recall_at_5", "mrr_at_5", "ndcg_at_5")}
    categories = {}
    for category in sorted({r["category"] for r in rows}):
        part = [r for r in rows if r["category"] == category]
        categories[category] = {"count": len(part),
            "correct_decision_proxy": mean((r["correct_answer_proxy"] if r["answerable"] else r["abstained"]) for r in part)}
    summary["categories"] = categories
    return summary


def evaluate(corpus_path, queries_path, lexicon_path, output, split="test"):
    corpus, queries = read_jsonl(corpus_path), read_jsonl(queries_path)
    checks = validate(corpus, queries)
    lexicon = json.loads(Path(lexicon_path).read_text(encoding="utf-8"))
    index = SearchIndex(corpus, lexicon)
    dev = [q for q in queries if q["split"] == "dev"]
    selected = [q for q in queries if q["split"] == split]
    rows, summaries, calibrations = {}, {}, {}
    for method in METHODS:
        threshold, calibration = calibration_threshold(index, dev, method)
        calibrations[method] = calibration
        rows[method] = evaluate_method(index, selected, method, threshold)
        summaries[method] = {"threshold": threshold, **summarise(rows[method])}
    difference_rows = []
    baseline = {r["id"]: r for r in rows["bm25"]}
    for row in rows["reranked"]:
        if row["answerable"]:
            difference_rows.append({"group": row["group"], "delta_mrr": row["mrr_at_5"] - baseline[row["id"]]["mrr_at_5"]})
    controls = []
    for plan in ("starter", "growth", "enterprise"):
        for question in ["production root access credential DEMO", "annual refund 60-day archived policy", "SCIM enterprise provisioning"]:
            for method in METHODS:
                hits, _ = index.rank(question, method, plan)
                controls.append(all(h["id"] in index.eligible_ids(plan) for h in hits))
    gates = {"valid_schema_and_disjoint_intent_groups": checks["split_overlap"] == 0,
             "eligibility_controls_27_of_27": all(controls) and len(controls) == 27,
             "no_restricted_or_archived_ranked_hits": all(s["eligibility_violations"] == 0 for s in summaries.values()),
             "answered_text_is_verbatim_source": all(r["quote_integrity"] for rr in rows.values() for r in rr)}
    report = {"schema_version": 1, "project_version": __version__, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(), "split": split,
        "data_origin": "original fictional support fixture; not customer data", "answer_mode": "verbatim_source_excerpt",
        "dataset": checks, "fingerprints": {"corpus": fingerprint(corpus_path), "queries": fingerprint(queries_path),
                                              "lexicon": fingerprint(lexicon_path)},
        "calibration_split": "dev", "calibration": calibrations, "methods": summaries,
        "paired_reranked_minus_bm25_mrr": {"difference": mean(r["delta_mrr"] for r in difference_rows),
                                          "cluster_bootstrap_95_ci": cluster_interval(difference_rows, "delta_mrr")},
        "engineering_checks": gates,
        "quality_interpretation": "Engineering checks do not certify answer quality. Inspect false answers and coverage.",
        "results": rows}
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "benchmark.json", report)
    fields = ["method", "id", "category", "question", "failure", "relevant_ids", "ranked_ids", "support_score", "answer"]
    with (out / "failures.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for method, rr in rows.items():
            for row in rr:
                if row["failure"]:
                    writer.writerow({field: method if field == "method" else
                                     json.dumps(row[field]) if isinstance(row[field], list) else row[field] for field in fields})
    write_json(out / "run_manifest.json", {k: report[k] for k in
        ("project_version", "created_at_utc", "python", "platform", "split", "fingerprints", "answer_mode")})
    return report


def score_external_predictions(corpus_path, queries_path, predictions_path, split="test"):
    """Score user-supplied model outputs without pretending to infer entailment."""
    corpus, queries = read_jsonl(corpus_path), read_jsonl(queries_path)
    validate(corpus, queries)
    queries = {q["id"]: q for q in queries if q["split"] == split}
    docs = {d["id"]: d for d in corpus}
    predictions = read_jsonl(predictions_path)
    seen, results = set(), []
    for prediction in predictions:
        key = prediction.get("id")
        if key not in queries or key in seen:
            raise ValueError("Prediction IDs must be unique and belong to the selected split")
        if not isinstance(prediction.get("answer"), str) or type(prediction.get("abstained")) is not bool:
            raise ValueError("Predictions need an answer string and boolean abstained")
        citations = prediction.get("citation_ids")
        if not isinstance(citations, list) or not all(isinstance(x, str) for x in citations) or len(set(citations)) != len(citations):
            raise ValueError("citation_ids must be a list of unique strings")
        if prediction["abstained"] and citations:
            raise ValueError("Abstained predictions must not have citations")
        seen.add(key)
        q = queries[key]
        eligible = all(c in docs and docs[c]["status"] == "current" and docs[c]["visibility"] == "public" and q["plan"] in docs[c]["plans"] for c in citations)
        cited_relevant = bool(citations and set(citations) <= set(q["relevant_ids"]))
        answered = not prediction["abstained"]
        span = bool(q["answer_phrase"] and q["answer_phrase"].casefold() in prediction["answer"].casefold())
        # A substring and relevant citation can coexist with an extra false claim.
        # Deliberately call this a proxy, never groundedness or semantic correctness.
        results.append({"id": key, "answerable": bool(q["relevant_ids"]), "answered": answered,
                        "citation_integrity": bool(citations and eligible) if answered else None,
                        "expected_span_and_relevant_citation_proxy": bool(answered and eligible and cited_relevant and span),
                        "needs_human_semantic_review": answered})
    if set(queries) != seen:
        raise ValueError("Provide exactly one prediction for every query in the selected split")
    return {"split": split, "predictions": len(results), "results": results,
            "warning": "This checks source IDs, eligibility and expected spans only. It does not establish semantic faithfulness."}

