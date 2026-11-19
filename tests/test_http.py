from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ragbench.server import make_handler

ROOT = Path(__file__).resolve().parent.parent


class HttpIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def test_health(self):
        with urlopen(self.base + "/health", timeout=5) as response:
            self.assertEqual(json.load(response)["status"], "ok")

    def test_live_search_returns_eligible_source_excerpt(self):
        request = Request(self.base + "/api/search", method="POST", headers={"Content-Type": "application/json"},
            data=json.dumps({"question": "How do I rotate an API key without interrupting integrations?"}).encode())
        with urlopen(request, timeout=5) as response:
            result = json.load(response)
        self.assertFalse(result["abstained"])
        self.assertEqual(result["citation"]["id"], "api-rotation")
        self.assertIn("create a second key", result["answer"])

    def test_unknown_route_does_not_expose_files(self):
        with self.assertRaises(HTTPError) as result:
            urlopen(self.base + "/data/corpus.jsonl", timeout=5)
        self.assertEqual(result.exception.code, 404)

    def test_role_override_rejected(self):
        request = Request(self.base + "/api/search", method="POST", headers={"Content-Type": "application/json"},
            data=b'{"question":"root secret","role":"internal"}')
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 400)

    def test_malformed_json_rejected(self):
        request = Request(self.base + "/api/search", method="POST", data=b'{broken')
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 400)

    def test_oversized_body_rejected(self):
        request = Request(self.base + "/api/search", method="POST", data=b'x' * 17000)
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 413)


if __name__ == "__main__":
    unittest.main()

