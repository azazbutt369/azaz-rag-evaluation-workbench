# Local demonstration API

Run `python -m ragbench serve`. Default address: `127.0.0.1:8765`.

| Route | Behaviour |
|---|---|
| GET / | Local workbench UI |
| GET /health | JSON readiness response |
| GET /api/report | Committed measured benchmark and per-query cases |
| POST /api/search | Run the selected local retrieval method |

POST accepts only `question` (1 to 2000 characters), `method` (`bm25`, `hybrid`,
`reranked`) and `plan` (`starter`, `growth`, `enterprise`). The body limit is
16,384 bytes. Role and visibility fields are rejected. Every search uses public,
current documents eligible for the selected demo plan. Plan selection is a
simulation, not authenticated entitlement enforcement.

Successful search responses contain the question, method, plan, threshold,
abstained flag, answer, optional citation, source hits and local scoring latency.
The answer is a complete verbatim excerpt, not a model completion. The score
is a heuristic evidence score and must not be labelled a probability.

Invalid requests return 400, excessive or empty bodies return 413, and unknown
routes return 404. Responses are JSON except the root HTML page. The server does
not write request bodies or question text to its log. It does not expose a file
browser or arbitrary path handler.

Use this only as a local demonstration. Production work needs authenticated
identity, server-side tenant/plan resolution, persistent versioned indexes,
audited access, TLS, a hardened application server, concurrency/load tests,
monitoring and deployment-specific review. Do not bind it to a public interface
and represent it as a deployed production system.

