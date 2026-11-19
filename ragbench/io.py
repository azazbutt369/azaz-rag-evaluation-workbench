"""Strict, small JSONL contracts. No evaluation labels enter retrieval."""
import hashlib
import json
from pathlib import Path

PLANS = {"starter", "growth", "enterprise"}


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{Path(path).name}:{number}: invalid JSON") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"{Path(path).name}:{number}: expected an object")
                rows.append(row)
    return rows


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def validate(corpus, queries):
    if not corpus or not queries:
        raise ValueError("Corpus and queries must both be non-empty")
    doc_ids, query_ids, groups, texts = set(), set(), {}, {}
    for doc in corpus:
        for field in ("id", "title", "text", "topic", "status", "visibility", "plans"):
            if field not in doc:
                raise ValueError(f"Document is missing {field}")
        if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("id", "title", "text", "topic")):
            raise ValueError("Document identifiers and text must be non-empty strings")
        if doc["id"] in doc_ids:
            raise ValueError("Duplicate document ID")
        doc_ids.add(doc["id"])
        if doc["status"] not in {"current", "archived"} or doc["visibility"] not in {"public", "internal"}:
            raise ValueError("Invalid document status or visibility")
        if not isinstance(doc["plans"], list) or not doc["plans"] or not set(doc["plans"]) <= PLANS:
            raise ValueError("Invalid document plans")
    by_id = {d["id"]: d for d in corpus}
    for query in queries:
        for field in ("id", "question", "group", "split", "plan", "relevant_ids", "answer_phrase", "category"):
            if field not in query:
                raise ValueError(f"Query is missing {field}")
        if not all(isinstance(query[k], str) and query[k].strip() for k in ("id", "question", "group", "category")):
            raise ValueError("Query identifiers and text must be non-empty strings")
        if query["id"] in query_ids:
            raise ValueError("Duplicate query ID")
        query_ids.add(query["id"])
        if query["split"] not in {"dev", "test"} or query["plan"] not in PLANS:
            raise ValueError("Invalid query split or plan")
        if query["group"] in groups and groups[query["group"]] != query["split"]:
            raise ValueError("Query intent group crosses development/test split")
        groups[query["group"]] = query["split"]
        normal = " ".join(query["question"].lower().split())
        if normal in texts:
            raise ValueError("Duplicate question text")
        texts[normal] = query["split"]
        refs = query["relevant_ids"]
        if not isinstance(refs, list) or len(set(refs)) != len(refs) or not set(refs) <= doc_ids:
            raise ValueError("Invalid relevant document IDs")
        if not isinstance(query["answer_phrase"], str) or bool(refs) != bool(query["answer_phrase"]):
            raise ValueError("Answerable queries need an answer phrase; negative queries must not have one")
        for ref in refs:
            doc = by_id[ref]
            if doc["status"] != "current" or doc["visibility"] != "public" or query["plan"] not in doc["plans"]:
                raise ValueError("Gold document is not eligible for this query")
        if refs and not any(query["answer_phrase"].casefold() in by_id[x]["text"].casefold() for x in refs):
            raise ValueError("Gold answer phrase must occur in a relevant source")
    for split in ("dev", "test"):
        rows = [q for q in queries if q["split"] == split]
        if not rows or not any(q["relevant_ids"] for q in rows) or not any(not q["relevant_ids"] for q in rows):
            raise ValueError("Both splits need answerable and unanswerable cases")
    return {"documents": len(corpus), "queries": len(queries), "intent_groups": len(groups),
            "split_overlap": 0, "duplicate_questions": 0}

