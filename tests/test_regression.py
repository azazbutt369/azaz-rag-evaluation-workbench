"""A successful aggregate comparison must not hide changed case decisions."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("regression", ROOT / "scripts/check_regression.py")
regression = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regression)


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.reference = json.loads((ROOT / "reports/benchmark.json").read_text(encoding="utf-8"))
        self.candidate = copy.deepcopy(self.reference)

    def test_identical_quality_ignores_timing_and_timestamp(self):
        self.candidate["created_at_utc"] = "different-run"
        self.candidate["results"]["hybrid"][0]["latency_ms"] = 999
        self.assertEqual(regression.compare(self.reference, self.candidate), [])

    def test_changed_ranking_detected_when_summaries_unchanged(self):
        row = self.candidate["results"]["hybrid"][0]
        row["ranked_ids"] = list(reversed(row["ranked_ids"]))
        self.assertIn(f"hybrid.{row['id']}.ranked_ids", regression.compare(self.reference, self.candidate))

    def test_missing_case_detected(self):
        self.candidate["results"]["hybrid"].pop()
        self.assertIn("hybrid.case_ids", regression.compare(self.reference, self.candidate))

    def test_duplicate_case_detected(self):
        self.candidate["results"]["hybrid"].append(self.candidate["results"]["hybrid"][0])
        self.assertIn("hybrid.duplicate_case_ids", regression.compare(self.reference, self.candidate))

    def test_changed_citation_detected(self):
        row = self.candidate["results"]["hybrid"][0]
        row["citation"] = {"id": "private-root", "title": "Injected invalid source"}
        self.assertIn(f"hybrid.{row['id']}.citation", regression.compare(self.reference, self.candidate))

    def test_failed_engineering_control_never_passes(self):
        for report in [self.reference, self.candidate]:
            report["engineering_checks"]["no_restricted_or_archived_ranked_hits"] = False
        self.assertTrue(regression.compare(self.reference, self.candidate))
