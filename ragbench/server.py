"""Local, public-persona demonstration API. No remote model calls."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .evaluation import METHODS
from .io import read_jsonl, validate
from .retrieval import SearchIndex


def validate_request(data):
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    if set(data) - {"question", "method", "plan"}:
        raise ValueError("Unexpected field; role and visibility cannot be supplied")
    question = data.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError("Question must contain 1 to 2000 characters")
    method, plan = data.get("method", "reranked"), data.get("plan", "growth")
    if method not in METHODS or plan not in {"starter", "growth", "enterprise"}:
        raise ValueError("Invalid method or plan")
    return question.strip(), method, plan


def make_handler(root):
    root = Path(root)
    corpus, questions = read_jsonl(root / "data/corpus.jsonl"), read_jsonl(root / "data/queries.jsonl")
    validate(corpus, questions)
    index = SearchIndex(corpus, json.loads((root / "data/lexicon.json").read_text(encoding="utf-8")))
    report = json.loads((root / "reports/benchmark.json").read_text(encoding="utf-8"))

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, data, content_type="application/json; charset=utf-8"):
            body = data if isinstance(data, bytes) else json.dumps(data, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/":
                self.respond(200, (root / "web/index.html").read_bytes(), "text/html; charset=utf-8")
            elif route == "/health":
                self.respond(200, {"status": "ok", "mode": "local_extractive_prototype"})
            elif route == "/api/report":
                self.respond(200, report)
            else:
                self.respond(404, {"error": "Route not found"})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/search":
                self.respond(404, {"error": "Route not found"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 16384:
                    self.respond(413, {"error": "Request body must contain 1 to 16384 bytes"})
                    return
                question, method, plan = validate_request(json.loads(self.rfile.read(size)))
                result = index.answer(question, method, plan, report["methods"][method]["threshold"])
                self.respond(200, result)
            except (ValueError, TypeError, UnicodeDecodeError):
                self.respond(400, {"error": "Invalid request. Supply question, method and plan; no other fields."})

        def log_message(self, fmt, *args):
            # Do not log request bodies or client question text.
            return

    return Handler


def serve(root, port=8765):
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(root))
    httpd.daemon_threads = True
    print(f"Local prototype: http://127.0.0.1:{port} (Ctrl+C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

