"""BM25, sparse hybrid retrieval and a transparent feature reranker.

The hybrid is lexical BM25 plus character-trigram TF-IDF, not dense embeddings.
The feature reranker is deterministic, not a neural cross-encoder.
"""
from collections import Counter
import math
import re
import time

STOP = set("a an the to for of is are was were be been in on at by and or with from it i we you my our your do does can could would should how what which when where why as if this that there have has get me please about much any all will".split())


def tokens(text):
    return [x for x in re.findall(r"[a-z0-9]+", text.casefold()) if x not in STOP]


def trigrams(text):
    # Character boundaries preserve local spelling while supporting small variants.
    words = tokens(text)
    return Counter(tri for word in words for tri in (f" {word} "[i:i+3] for i in range(max(0, len(word)))))


def reciprocal_rank_fusion(rankings, constant=60):
    scores = Counter()
    for ranking in rankings:
        for rank, identifier in enumerate(ranking, 1):
            scores[identifier] += 1 / (constant + rank)
    return scores


class SearchIndex:
    def __init__(self, documents, lexicon=None):
        self.documents = {d["id"]: d for d in documents}
        self.lexicon = lexicon or {}
        self.words = {d["id"]: Counter(tokens(d["title"] + " " + d["text"])) for d in documents}
        self.lengths = {key: sum(value.values()) for key, value in self.words.items()}
        self.avg_length = sum(self.lengths.values()) / max(1, len(self.lengths))
        document_frequency = Counter(t for word in self.words.values() for t in word)
        count = len(documents)
        self.idf = {t: math.log(1 + (count - n + .5) / (n + .5)) for t, n in document_frequency.items()}
        self.title_words = {d["id"]: set(tokens(d["title"])) for d in documents}
        char_counts = {d["id"]: trigrams(d["title"] + " " + d["text"]) for d in documents}
        frequencies = Counter(t for word in char_counts.values() for t in word)
        self.char_idf = {t: math.log((1 + count) / (1 + n)) + 1 for t, n in frequencies.items()}
        self.char_vectors = {key: self._vector(value) for key, value in char_counts.items()}

    def _vector(self, counts):
        vector = {key: (1 + math.log(value)) * self.char_idf.get(key, 0) for key, value in counts.items()}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1
        return {key: value / norm for key, value in vector.items()}

    def expand(self, question):
        question = question.casefold()
        additions = [value for key, value in self.lexicon.items()
                     if re.search(r"\b" + re.escape(key) + r"\b", question)]
        return question + " " + " ".join(additions)

    def eligible_ids(self, plan="growth"):
        # The persona is public only. No caller-controlled role can grant access.
        return [key for key, doc in self.documents.items()
                if doc["status"] == "current" and doc["visibility"] == "public" and plan in doc["plans"]]

    def bm25(self, question, identifiers):
        result = {}
        for key in identifiers:
            score = 0.0
            length = self.lengths[key]
            for token in set(tokens(question)):
                frequency = self.words[key].get(token, 0)
                if frequency:
                    score += self.idf[token] * frequency * 2.5 / (frequency + 1.5 * (.25 + .75 * length / self.avg_length))
            result[key] = score
        return result

    def rank(self, question, method="reranked", plan="growth", top_k=5):
        if method not in {"bm25", "hybrid", "reranked"}:
            raise ValueError("Unknown retrieval method")
        if plan not in {"starter", "growth", "enterprise"}:
            raise ValueError("Unknown plan")
        started = time.perf_counter()
        eligible = self.eligible_ids(plan)
        expanded = self.expand(question) if method != "bm25" else question
        lexical = self.bm25(expanded, eligible)
        bm_rank = sorted(eligible, key=lambda x: (-lexical[x], x))
        char_query = self._vector(trigrams(expanded))
        char_scores = {key: sum(value * self.char_vectors[key].get(t, 0) for t, value in char_query.items()) for key in eligible}
        scores = lexical
        if method != "bm25":
            char_rank = sorted(eligible, key=lambda x: (-char_scores[x], x))
            # Zero-signal documents must not acquire artificial RRF evidence.
            positive_bm = [x for x in bm_rank if lexical[x] > 0]
            positive_char = [x for x in char_rank if char_scores[x] > 0]
            fused = reciprocal_rank_fusion([positive_bm, positive_char])
            candidates = sorted(fused, key=lambda x: (-fused[x], x))
            scores = dict(fused)
            if method == "reranked":
                words = set(tokens(expanded))
                # Only score the top 12 fused candidates. No relevance labels are visible here.
                candidates = candidates[:12]
                scores = {}
                for key in candidates:
                    coverage = len(words & self.words[key].keys()) / max(1, len(words))
                    title = len(words & self.title_words[key]) / max(1, len(words))
                    scores[key] = .35 * coverage + .35 * title + .20 * char_scores[key] + .10 * fused[key] * 30.5
            bm_rank = sorted(candidates, key=lambda x: (-scores[x], x))
        hits = []
        for key in bm_rank[:top_k]:
            doc = self.documents[key]
            qwords = set(tokens(expanded))
            coverage = len(qwords & self.words[key].keys()) / max(1, len(qwords))
            title = len(qwords & self.title_words[key]) / max(1, len(qwords))
            # A heuristic evidence score, not a calibrated probability or semantic entailment test.
            support = .55 * coverage + .25 * title + .20 * char_scores[key]
            hits.append({"id": key, "title": doc["title"], "text": doc["text"],
                         "score": round(scores.get(key, 0), 8), "support_score": round(support, 8),
                         "coverage": round(coverage, 6)})
        return hits, (time.perf_counter() - started) * 1000

    def answer(self, question, method="reranked", plan="growth", threshold=.5, top_k=5):
        hits, elapsed = self.rank(question, method, plan, top_k)
        accepted = bool(hits and hits[0]["support_score"] >= threshold and hits[0]["score"] > 0)
        first = hits[0] if hits else None
        return {"question": question, "method": method, "plan": plan, "threshold": threshold,
                "abstained": not accepted,
                "answer": first["text"] if accepted else "I do not have sufficient evidence in the eligible knowledge base to answer this question.",
                "citation": {"id": first["id"], "title": first["title"]} if accepted else None,
                "answer_mode": "verbatim_source_excerpt", "hits": hits, "latency_ms": elapsed}

