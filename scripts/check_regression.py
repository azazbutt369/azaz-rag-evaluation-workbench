"""Compare a rerun with the committed evidence, ignoring timing and timestamps."""
import json
from pathlib import Path
import sys

FIELDS = ("threshold", "recall_at_1", "recall_at_5", "mrr_at_5", "ndcg_at_5",
          "answer_coverage_answerable", "correct_answer_rate_answerable",
          "false_answer_rate_unanswerable", "selective_answer_accuracy_proxy",
          "eligibility_violations", "failure_counts")

CASE_FIELDS = ("group", "category", "question", "plan", "answerable", "relevant_ids",
               "answer_phrase", "ranked_ids", "answer", "citation", "support_score",
               "abstained", "correct_answer_proxy", "quote_integrity",
               "eligibility_violation", "failure")


def compare(reference, candidate):
    errors = []
    for field in ("fingerprints", "split", "dataset", "calibration_split", "engineering_checks"):
        if reference[field] != candidate[field]:
            errors.append(field)
    for method in ("bm25", "hybrid", "reranked"):
        for field in FIELDS:
            if reference["methods"][method][field] != candidate["methods"][method][field]:
                errors.append(f"{method}.{field}")
        # Equal aggregate metrics can hide different failures. Reproduction
        # requires the same case decisions as well as the same summary.
        ref_rows = reference["results"][method]
        cand_rows = candidate["results"][method]
        ref = {row["id"]: row for row in ref_rows}
        cand = {row["id"]: row for row in cand_rows}
        if len(ref) != len(ref_rows) or len(cand) != len(cand_rows):
            errors.append(f"{method}.duplicate_case_ids")
        if set(ref) != set(cand):
            errors.append(f"{method}.case_ids")
        for key in sorted(set(ref) & set(cand)):
            for field in CASE_FIELDS:
                if ref[key].get(field) != cand[key].get(field):
                    errors.append(f"{method}.{key}.{field}")
        if not all(candidate["engineering_checks"].values()):
            errors.append(f"{method}.failed_engineering_checks")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/check_regression.py REFERENCE_JSON CANDIDATE_JSON")
    errors = compare(*(json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:]))
    if errors:
        raise SystemExit("Evidence changed: " + ", ".join(errors))
    print("PASS: dataset, thresholds, quality metrics, per-case outputs and engineering checks reproduce exactly.")

