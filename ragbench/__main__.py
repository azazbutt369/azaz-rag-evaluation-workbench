import argparse
import json
from pathlib import Path
import sys

from .evaluation import METHODS, evaluate, score_external_predictions
from .io import read_jsonl, validate, write_json
from .reporting import create_reports
from .retrieval import SearchIndex

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Offline retrieval evaluation workbench. No API key required.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Project directory containing data/, web/ and reports/")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("benchmark", help="Calibrate on dev; evaluate the selected split")
    bench.add_argument("--split", choices=["dev", "test"], default="test")
    bench.add_argument("--output", type=Path, default=None)
    bench.add_argument("--check", action="store_true", help="Exit nonzero if engineering checks fail")
    sub.add_parser("validate", help="Validate corpus, qrels, answer spans and split integrity")
    query = sub.add_parser("query", help="Retrieve and quote an eligible source")
    query.add_argument("question")
    query.add_argument("--method", choices=METHODS, default="reranked")
    query.add_argument("--plan", choices=["starter", "growth", "enterprise"], default="growth")
    server = sub.add_parser("serve", help="Start the local demo on 127.0.0.1 only")
    server.add_argument("--port", type=int, default=8765)
    external = sub.add_parser("score-responses", help="Check complete user-supplied model output JSONL")
    external.add_argument("predictions", type=Path)
    external.add_argument("--split", choices=["dev", "test"], default="test")
    external.add_argument("--output", type=Path, default=Path("reports/external_response_checks.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    corpus, queries, lexicon = root / "data/corpus.jsonl", root / "data/queries.jsonl", root / "data/lexicon.json"
    try:
        if args.command == "validate":
            print(json.dumps(validate(read_jsonl(corpus), read_jsonl(queries)), indent=2))
        elif args.command == "benchmark":
            output = args.output or root / "reports"
            report = evaluate(corpus, queries, lexicon, output, args.split)
            if output.resolve() == (root / "reports").resolve():
                create_reports(root, report)
            print(json.dumps({"split": report["split"], "methods": report["methods"], "engineering_checks": report["engineering_checks"]}, indent=2))
            if args.check and not all(report["engineering_checks"].values()):
                return 1
        elif args.command == "query":
            report = json.loads((root / "reports/benchmark.json").read_text(encoding="utf-8"))
            index = SearchIndex(read_jsonl(corpus), json.loads(lexicon.read_text(encoding="utf-8")))
            print(json.dumps(index.answer(args.question, args.method, args.plan,
                       report["methods"][args.method]["threshold"]), indent=2))
        elif args.command == "serve":
            from .server import serve
            serve(root, args.port)
        elif args.command == "score-responses":
            result = score_external_predictions(corpus, queries, args.predictions, args.split)
            write_json(args.output, result)
            print(json.dumps({"output": str(args.output), "predictions": result["predictions"], "warning": result["warning"]}, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

