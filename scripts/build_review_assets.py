"""Build measured review examples and deliberate control demonstrations.

Run from the extracted project directory after a benchmark. No ranking,
fixture, threshold or lexicon is modified by this script.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ragbench.io import read_jsonl, validate, write_json
from ragbench.evaluation import score_external_predictions
from check_regression import compare


def main():
    report = json.loads((ROOT / "reports/benchmark.json").read_text(encoding="utf-8"))
    corpus = read_jsonl(ROOT / "data/corpus.jsonl")
    queries = read_jsonl(ROOT / "data/queries.jsonl")
    hybrid = report["results"]["hybrid"]
    hm = {r["id"]: r for r in hybrid}
    bm = {r["id"]: r for r in report["results"]["bm25"]}
    selections = [
        ("Supported source excerpt", "hybrid", next(r for r in hybrid if r["correct_answer_proxy"])),
        ("Unknown fact: abstention", "hybrid", next(r for r in hybrid if not r["answerable"])),
        ("Wrong source despite a relevant top-five hit", "hybrid", next(r for r in hybrid if r["failure"] == "wrong_source_or_span")),
        ("Useful source rejected by the gate", "hybrid", next(r for r in hybrid if r["failure"] == "abstained_answerable")),
        ("Reranking regression", "reranked", next(r for r in report["results"]["reranked"] if r["answerable"] and r["mrr_at_5"] < hm[r["id"]]["mrr_at_5"])),
        ("Hybrid answers a baseline false abstention", "hybrid", next(r for r in hybrid if r["correct_answer_proxy"] and not bm[r["id"]]["correct_answer_proxy"]))]
    examples = []
    for title, method, row in selections:
        result = {k: v for k, v in row.items() if k != "latency_ms"}
        examples.append({"title": title, "method": method, "threshold": report["methods"][method]["threshold"],
                         "observed_result": result})
    write_json(ROOT / "reports/sample_outputs.json", {
        "origin": "Actual outputs from the committed authored synthetic test fixture. Examples selected after inspection; not a separate evaluation set.",
        "benchmark_sha256": hashlib.sha256((ROOT / "reports/benchmark.json").read_bytes()).hexdigest(),
        "examples": examples})
    # Complete adapter input, built from the actual extractive hybrid outputs.
    # This is a format demonstration, not an external model inference run.
    predictions = [{"id": r["id"], "answer": r["answer"],
                    "citation_ids": [r["citation"]["id"]] if r["citation"] else [],
                    "abstained": r["abstained"]} for r in hybrid]
    path = ROOT / "examples/demo_extractive_responses.jsonl"
    path.parent.mkdir(exist_ok=True)
    path.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in predictions), encoding="utf-8")
    checks = score_external_predictions(ROOT / "data/corpus.jsonl", ROOT / "data/queries.jsonl", path)
    checks["origin"] = "Extractive hybrid demo outputs; not externally generated LLM responses"
    write_json(ROOT / "reports/demo_response_checks.json", checks)
    md = ["# Inspected sample outputs", "", "Actual test outputs from the fictional NorthstarFlow fixture. These examples were selected after observing the benchmark to illustrate success and failure. All 48 test cases per method remain available in reports/index.html and benchmark.json.", ""]
    for item in examples:
        r = item["observed_result"]
        md += ["## " + item["title"], "", f"Question: {r['question']}", "",
               f"Case: `{r['id']}` | Method: `{item['method']}` | Answerable: {r['answerable']} | Abstained: {r['abstained']}", "",
               "Observed response:", "", "> " + r["answer"], "",
               f"Citation: {r['citation']['id'] if r['citation'] else 'none'}; expected source: {', '.join(r['relevant_ids']) or 'none'}.",
               f"Returned order: {', '.join(r['ranked_ids'])}.",
               f"Evidence score: {r['support_score']:.6f}; selected development threshold: {item['threshold']:.2f}. This score is not a probability.", ""]
    md += ["The source-and-substring correctness proxy does not assess semantic faithfulness or the completeness of a generated response. No live LLM was used.", ""]
    (ROOT / "docs/SAMPLE_OUTPUTS.md").write_text("\n".join(md), encoding="utf-8")

    demonstrations = []
    def record(name, c, q):
        try:
            validate(c, q)
            demonstrations.append({"control": name, "deliberately_contaminated": True, "detected": False})
        except ValueError as exc:
            demonstrations.append({"control": name, "deliberately_contaminated": True, "detected": True, "message": str(exc)})
    q = copy.deepcopy(queries)
    next(r for r in q if r["split"] == "test")["group"] = next(r["group"] for r in q if r["split"] == "dev")
    record("Cross-split intent-group contamination", corpus, q)
    q = copy.deepcopy(queries)
    q[1]["question"] = q[0]["question"]
    record("Duplicate evaluation question", corpus, q)
    c = copy.deepcopy(corpus)
    ref = next(q["relevant_ids"][0] for q in queries if q["relevant_ids"])
    next(d for d in c if d["id"] == ref)["visibility"] = "internal"
    record("Gold source becomes ineligible", c, queries)
    mutated = copy.deepcopy(report)
    mutated["results"]["hybrid"][0]["ranked_ids"].reverse()
    errors = compare(report, mutated)
    demonstrations.append({"control": "Changed per-case ranking while aggregate summaries remain unchanged",
                           "deliberately_contaminated": True, "detected": bool(errors), "messages": errors})
    manifest = json.loads((ROOT / "data/frozen_manifest.json").read_text(encoding="utf-8"))
    frozen = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == expected for p, expected in manifest["hashes"].items()}
    controls = {"clean_fixture": validate(corpus, queries), "frozen_original_inputs_and_methods": frozen,
                "demonstrations": demonstrations,
                "limits": "Injected examples prove these named controls fire, not exhaustive leakage detection, tenant security or prompt-injection protection."}
    write_json(ROOT / "reports/control_demonstrations.json", controls)
    if not all(frozen.values()) or not all(d["detected"] for d in demonstrations):
        raise SystemExit("Control demonstration or frozen method check failed")
    print(f"Built {len(examples)} measured examples; {len(demonstrations)} deliberate faults detected; all original fixture/method hashes unchanged.")


if __name__ == "__main__":
    main()
