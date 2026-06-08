"""Tests for user-facing token savings metrics."""

from __future__ import annotations

import unittest

from app import (
    COMPACT_REPORT_INSTRUCTIONS,
    DETAILED_REPORT_INSTRUCTIONS,
    apply_analysis_detail_preference,
    calculate_savings_metrics,
    estimate_tokens,
    token_estimation_profile,
)


class TokenSavingsMetricsTest(unittest.TestCase):
    def test_reports_positive_savings_when_context_is_shorter(self) -> None:
        metrics = calculate_savings_metrics("a" * 400, "b" * 100)

        self.assertEqual(metrics["original_tokens"], 100)
        self.assertEqual(metrics["used_context_tokens"], 25)
        self.assertEqual(metrics["token_delta"], 75)
        self.assertEqual(metrics["saved_tokens"], 75)
        self.assertEqual(metrics["savings_percent"], 75)
        self.assertTrue(metrics["has_savings"])

    def test_reports_negative_savings_when_context_is_longer(self) -> None:
        metrics = calculate_savings_metrics("a" * 400, "b" * 500)

        self.assertEqual(metrics["original_tokens"], 100)
        self.assertEqual(metrics["used_context_tokens"], 125)
        self.assertEqual(metrics["token_delta"], -25)
        self.assertEqual(metrics["saved_tokens"], 0)
        self.assertEqual(metrics["savings_percent"], -25)
        self.assertFalse(metrics["has_savings"])

    def test_matches_user_reported_overuse_example(self) -> None:
        metrics = calculate_savings_metrics("a" * 6788, "b" * 7680)

        self.assertEqual(metrics["original_tokens"], 1697)
        self.assertEqual(metrics["used_context_tokens"], 1920)
        self.assertEqual(metrics["token_delta"], -223)
        self.assertAlmostEqual(metrics["savings_percent"], -13.1408, places=4)
        self.assertFalse(metrics["has_savings"])

    def test_uses_model_profile_for_estimates(self) -> None:
        self.assertEqual(estimate_tokens("a" * 380, "gpt-5.4-mini"), 100)
        self.assertEqual(estimate_tokens("a" * 340, "gpt-4"), 100)

        profile = token_estimation_profile("gpt-5.4-mini")
        self.assertEqual(profile["name"], "o200k/GPT-4o- und GPT-5-Profil")

    def test_uses_exact_completion_tokens_when_available(self) -> None:
        metrics = calculate_savings_metrics(
            "a" * 380,
            "b" * 1000,
            model="gpt-5.4-mini",
            used_context_tokens=42,
        )

        self.assertEqual(metrics["original_tokens"], 100)
        self.assertEqual(metrics["used_context_tokens"], 42)
        self.assertEqual(metrics["used_context_token_source"], "api_completion_tokens")
        self.assertEqual(metrics["token_delta"], 58)


class AnalysisDetailPreferenceTest(unittest.TestCase):
    def test_appends_compact_instruction_by_default(self) -> None:
        prompt = apply_analysis_detail_preference("Analysiere: {document_blocks}", False)

        self.assertIn("Ausgabeumfang:", prompt)
        self.assertIn(COMPACT_REPORT_INSTRUCTIONS, prompt)
        self.assertNotIn(DETAILED_REPORT_INSTRUCTIONS, prompt)
        self.assertIn("{document_blocks}", prompt)

    def test_appends_detailed_instruction_when_enabled(self) -> None:
        prompt = apply_analysis_detail_preference("Analysiere: {document_blocks}", True)

        self.assertIn("Ausgabeumfang:", prompt)
        self.assertIn(DETAILED_REPORT_INSTRUCTIONS, prompt)
        self.assertNotIn(COMPACT_REPORT_INSTRUCTIONS, prompt)
        self.assertIn("{document_blocks}", prompt)


if __name__ == "__main__":
    unittest.main()
