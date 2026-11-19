import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from ragbench.evaluation import calibration_threshold, ranking_metrics, score_external_predictions
from ragbench.io import read_jsonl, validate
from ragbench.retrieval import SearchIndex, reciprocal_rank_fusion
from ragbench.server import validate_request

ROOT = Path(__file__).resolve().parent.parent


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = read_jsonl(ROOT / "data/corpus.jsonl")
        cls.questions = read_jsonl(ROOT / "data/queries.jsonl")
        cls.index = SearchIndex(cls.docs, json.loads((ROOT / "data/lexicon.json").read_text()))

    def test_fixture_is_valid(self):
        result = validate(self.docs, self.questions)
        self.assertEqual((result["documents"], result["queries"], result["intent_groups"]), (48, 96, 36))

    def test_known_ranking_metrics(self):
        result = ranking_metrics(["wrong", "right", "other"], ["right"])
        self.assertEqual(result["recall_at_1"], 0)
        self.assertEqual(result["recall_at_5"], 1)
        self.assertEqual(result["mrr_at_5"], .5)
        self.assertAlmostEqual(result["ndcg_at_5"], 1 / math.log2(3))

    def test_multiple_relevant_documents(self):
        result = ranking_metrics(["a", "x", "b"], ["a", "b"])
        self.assertEqual(result["recall_at_1"], .5)
        self.assertEqual(result["recall_at_5"], 1)
        self.assertAlmostEqual(result["ndcg_at_5"], (1 + .5) / (1 + 1 / math.log2(3)))

    def test_duplicate_hits_cannot_inflate_recall(self):
        self.assertEqual(ranking_metrics(["a", "a", "a"], ["a", "b"])["recall_at_5"], .5)

    def test_unanswerable_has_no_retrieval_metric(self):
        self.assertIsNone(ranking_metrics(["a"], []))

    def test_split_group_overlap_rejected(self):
        bad = copy.deepcopy(self.questions)
        bad[-1]["group"] = bad[0]["group"]
        with self.assertRaisesRegex(ValueError, "crosses"):
            validate(self.docs, bad)

    def test_duplicate_questions_rejected(self):
        bad = copy.deepcopy(self.questions)
        bad[-1]["question"] = bad[0]["question"]
        with self.assertRaisesRegex(ValueError, "Duplicate question"):
            validate(self.docs, bad)

    def test_gold_span_must_be_in_source(self):
        bad = copy.deepcopy(self.questions)
        bad[0]["answer_phrase"] = "invented absent figure"
        with self.assertRaisesRegex(ValueError, "Gold answer phrase"):
            validate(self.docs, bad)

    def test_unknown_gold_id_rejected(self):
        bad = copy.deepcopy(self.questions)
        bad[0]["relevant_ids"] = ["absent"]
        with self.assertRaisesRegex(ValueError, "relevant"):
            validate(self.docs, bad)

    def test_internal_sources_never_rank(self):
        for method in ("bm25", "hybrid", "reranked"):
            for plan in ("starter", "growth", "enterprise"):
                hits, _ = self.index.rank("production root access credential DEMO", method, plan, top_k=100)
                self.assertTrue(all(self.index.documents[h["id"]]["visibility"] == "public" for h in hits))

    def test_archived_sources_never_rank(self):
        for method in ("bm25", "hybrid", "reranked"):
            hits, _ = self.index.rank("archived annual refund 60 day", method, top_k=100)
            self.assertTrue(all(self.index.documents[h["id"]]["status"] == "current" for h in hits))

    def test_plan_filters_apply_to_every_method(self):
        for method in ("bm25", "hybrid", "reranked"):
            hits, _ = self.index.rank("SCIM provisioning details", method, "starter", 100)
            self.assertNotIn("scim", [h["id"] for h in hits])
        self.assertIn("scim", self.index.eligible_ids("enterprise"))

    def test_answer_is_exact_source_excerpt(self):
        response = self.index.answer("API key rotation", threshold=0)
        self.assertFalse(response["abstained"])
        self.assertEqual(response["answer"], self.index.documents[response["citation"]["id"]]["text"])

    def test_threshold_rejects_without_citation(self):
        result = self.index.answer("API key rotation", threshold=1.1)
        self.assertTrue(result["abstained"])
        self.assertIsNone(result["citation"])

    def test_zero_signal_query_abstains(self):
        result = self.index.answer("zzzzqqqq xxxxvvvv", "bm25", threshold=0)
        self.assertTrue(result["abstained"])

    def test_rrf_uses_rank_order(self):
        result = reciprocal_rank_fusion([["a", "b"], ["b", "a"]])
        self.assertEqual(result["a"], result["b"])

    def test_retrieval_has_no_query_label_input(self):
        self.assertNotIn("relevant_ids", self.index.__dict__)
        question = self.questions[0]["question"]
        a, _ = self.index.rank(question)
        labels = copy.deepcopy(self.questions)
        labels[0]["relevant_ids"] = []
        b, _ = self.index.rank(question)
        self.assertEqual(a, b)

    def test_calibration_is_reproducible(self):
        dev = [q for q in self.questions if q["split"] == "dev"]
        first = calibration_threshold(self.index, dev, "reranked")
        self.assertEqual(first, calibration_threshold(self.index, dev, "reranked"))
        self.assertEqual(first[1]["selection_split"], "dev")

    def test_server_rejects_role_injection(self):
        with self.assertRaises(ValueError):
            validate_request({"question": "secret", "role": "internal"})

    def test_server_rejects_bad_shapes(self):
        for data in [[], {}, {"question": 5}, {"question": "x", "plan": "root"}, {"question": "x" * 2001}]:
            with self.assertRaises(ValueError):
                validate_request(data)

    def test_external_predictions_require_complete_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            path.write_text(json.dumps({"id": "test-api-rotation-1", "answer": "x", "citation_ids": [], "abstained": False}) + "\n")
            with self.assertRaisesRegex(ValueError, "every query"):
                score_external_predictions(ROOT / "data/corpus.jsonl", ROOT / "data/queries.jsonl", path)

    def test_external_invalid_citation_is_flagged(self):
        predictions = [{"id": q["id"], "answer": "I cannot answer", "citation_ids": [], "abstained": True}
                       for q in self.questions if q["split"] == "test"]
        predictions[0].update(answer="create a second key", citation_ids=["private-root"], abstained=False)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            path.write_text("".join(json.dumps(p) + "\n" for p in predictions))
            result = score_external_predictions(ROOT / "data/corpus.jsonl", ROOT / "data/queries.jsonl", path)
        self.assertFalse(result["results"][0]["citation_integrity"])
        self.assertFalse(result["results"][0]["expected_span_and_relevant_citation_proxy"])


if __name__ == "__main__":
    unittest.main()

