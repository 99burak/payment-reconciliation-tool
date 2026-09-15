"""Verify complete reconciliation against fixtures and ambiguous input cases."""

import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path
import unittest

from reconciliation.engine import reconcile_payments
from reconciliation.models import ActualPayment, ExpectedPayment
from reconciliation.validation import load_actual_payments, load_expected_payments


class ReconciliationTests(unittest.TestCase):
    def test_all_sample_references_agree_with_the_expected_results(self):
        samples = Path(__file__).resolve().parents[1] / "samples"
        expected = load_expected_payments((samples / "expected_payments.csv").read_bytes())
        actual = load_actual_payments((samples / "actual_payments.csv").read_bytes())
        original_expected, original_actual = expected.copy(), actual.copy()
        results = reconcile_payments(expected, actual)
        with (samples / "expected_results.csv").open(encoding="utf-8-sig", newline="") as handle:
            reference = list(csv.DictReader(handle))

        self.assertEqual([r.payment_reference for r in results], [r["payment_reference"] for r in reference])
        for result, row in zip(results, reference, strict=True):
            with self.subTest(reference=result.payment_reference):
                self.assertEqual(result.status, row["status"])
                for field, csv_column in [
                    ("expected_amount_cents", "expected_amount"),
                    ("actual_amount_cents", "actual_amount"),
                    ("difference_cents", "difference"),
                ]:
                    wanted = int(Decimal(row[csv_column]) * 100) if row[csv_column] else None
                    self.assertEqual(getattr(result, field), wanted)
                self.assertEqual(len(result.expected_records), int(row["expected_count"]))
                self.assertEqual(len(result.actual_records), int(row["actual_count"]))
                self.assertTrue(result.description)

        self.assertEqual(Counter(r.status for r in results), {
            "matched": 2, "amount_mismatch": 2, "missing": 1, "unexpected": 1, "review_required": 2,
        })
        self.assertCountEqual([id(p) for r in results for p in r.expected_records], [id(p) for p in expected])
        self.assertCountEqual([id(p) for r in results for p in r.actual_records], [id(p) for p in actual])
        self.assertEqual(expected, original_expected)
        self.assertEqual(actual, original_actual)

    def test_duplicates_take_priority_and_are_never_summed(self):
        for expected_count, actual_count in [(2, 0), (0, 2), (2, 1), (1, 2), (2, 2)]:
            with self.subTest(expected_count=expected_count, actual_count=actual_count):
                # Each nonempty side totals 600 cents; duplicates must still require review.
                expected = [ExpectedPayment("P", "Company", 600 // expected_count, i + 2)
                            for i in range(expected_count)]
                actual = [ActualPayment(f"TX-{i}", "P", 600 // actual_count, i + 2)
                          for i in range(actual_count)]
                result = reconcile_payments(expected, actual)[0]
                self.assertEqual(result.status, "review_required")
                self.assertIsNone(result.expected_amount_cents)
                self.assertIsNone(result.actual_amount_cents)
                self.assertIsNone(result.difference_cents)
                self.assertEqual(result.expected_records, tuple(expected))
                self.assertEqual(result.actual_records, tuple(actual))
                if expected_count > 1:
                    self.assertIn("expected payments", result.description)
                if actual_count > 1:
                    self.assertIn("actual payments", result.description)

    def test_one_sided_inputs_keep_missing_values_distinct_from_zero(self):
        expected = [ExpectedPayment("P", "Company", 100, 2)]
        actual = [ActualPayment("TX-1", "P", 100, 2)]
        missing = reconcile_payments(expected, [])[0]
        self.assertEqual(missing.status, "missing")
        self.assertEqual(missing.expected_amount_cents, 100)
        self.assertIsNone(missing.actual_amount_cents)
        self.assertIsNone(missing.difference_cents)
        unexpected = reconcile_payments([], actual)[0]
        self.assertEqual(unexpected.status, "unexpected")
        self.assertIsNone(unexpected.expected_amount_cents)
        self.assertEqual(unexpected.actual_amount_cents, 100)
        self.assertIsNone(unexpected.difference_cents)

    def test_full_flow_preserves_one_cent_differences_and_describes_direction(self):
        for amount in (125075, 9_007_199_254_740_992):
            for offset in (-1, 0, 1):
                with self.subTest(amount=amount, offset=offset):
                    result = reconcile_payments(
                        [ExpectedPayment("P", "Company", amount, 2)],
                        [ActualPayment("TX-1", "P", amount + offset, 2)],
                    )[0]
                    self.assertEqual(result.difference_cents, offset)
                    self.assertEqual(result.status, "matched" if offset == 0 else "amount_mismatch")
                    if offset:
                        direction = "below" if offset < 0 else "above"
                        self.assertIn(f"0.01 TRY {direction}", result.description)

    def test_empty_inputs_have_no_results(self):
        self.assertEqual(reconcile_payments([], []), [])


if __name__ == "__main__":
    unittest.main()
