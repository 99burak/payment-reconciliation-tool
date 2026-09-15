"""Check reference grouping, duplicate detection, and source record preservation."""

import csv
from pathlib import Path
import unittest

from reconciliation.engine import group_payments_by_reference
from reconciliation.models import ActualPayment, ExpectedPayment
from reconciliation.validation import load_actual_payments, load_expected_payments


class PaymentGroupingTests(unittest.TestCase):
    def test_sample_groups_match_reference_counts_and_review_flags(self):
        samples = Path(__file__).resolve().parents[1] / "samples"
        expected = load_expected_payments((samples / "expected_payments.csv").read_bytes())
        actual = load_actual_payments((samples / "actual_payments.csv").read_bytes())
        groups = group_payments_by_reference(expected, actual)
        with (samples / "expected_results.csv").open(encoding="utf-8-sig", newline="") as handle:
            reference_counts = {
                row["payment_reference"]: (
                    int(row["expected_count"]), int(row["actual_count"]),
                    row["status"] == "review_required",
                )
                for row in csv.DictReader(handle)
            }
        self.assertEqual(len(groups), 8)
        self.assertEqual(
            {g.payment_reference: (len(g.expected_records), len(g.actual_records), g.requires_review)
             for g in groups},
            reference_counts,
        )
        # Verify every original object remains on its side, exactly once.
        self.assertCountEqual([id(r) for g in groups for r in g.expected_records], [id(r) for r in expected])
        self.assertCountEqual([id(r) for g in groups for r in g.actual_records], [id(r) for r in actual])

    def test_duplicates_on_either_side_require_review_even_without_a_counterpart(self):
        for expected_count, actual_count in [(2, 0), (0, 2), (2, 1), (1, 2), (2, 2)]:
            with self.subTest(expected_count=expected_count, actual_count=actual_count):
                expected = [ExpectedPayment("P", "Company", 100, i + 2) for i in range(expected_count)]
                actual = [ActualPayment(f"TX-{i}", "P", 100, i + 2) for i in range(actual_count)]
                group = group_payments_by_reference(expected, actual)[0]
                self.assertTrue(group.requires_review)
                self.assertEqual(group.expected_records, tuple(expected))
                self.assertEqual(group.actual_records, tuple(actual))

    def test_single_records_do_not_require_duplicate_review(self):
        for expected_count, actual_count in [(1, 0), (0, 1), (1, 1)]:
            with self.subTest(expected_count=expected_count, actual_count=actual_count):
                expected = [ExpectedPayment("P", "Company", 100, 2)] * expected_count
                actual = [ActualPayment("TX-1", "P", 200, 2)] * actual_count
                self.assertFalse(group_payments_by_reference(expected, actual)[0].requires_review)

    def test_duplicate_amounts_are_not_combined_even_if_the_sum_matches(self):
        expected = [ExpectedPayment("P", "Company", 60000, 2)]
        actual = [ActualPayment("TX-1", "P", 30000, 2), ActualPayment("TX-2", "P", 30000, 3)]
        group = group_payments_by_reference(expected, actual)[0]
        self.assertTrue(group.requires_review)
        self.assertEqual([r.amount_cents for r in group.actual_records], [30000, 30000])
        self.assertEqual([r.source_row for r in group.actual_records], [2, 3])

    def test_groups_preserve_first_seen_order_and_do_not_modify_inputs(self):
        expected = [ExpectedPayment("B", "First", 100, 2), ExpectedPayment("A", "Second", 200, 3),
                    ExpectedPayment("B", "Third", 300, 4)]
        actual = [ActualPayment("TX-1", "C", 400, 2), ActualPayment("TX-2", "A", 200, 3),
                  ActualPayment("TX-3", "D", 500, 4)]
        original_expected, original_actual = expected.copy(), actual.copy()
        groups = group_payments_by_reference(expected, actual)
        self.assertEqual([g.payment_reference for g in groups], ["B", "A", "C", "D"])
        self.assertEqual(groups[0].expected_records, (expected[0], expected[2]))
        self.assertEqual(expected, original_expected)
        self.assertEqual(actual, original_actual)

    def test_case_and_leading_zeros_keep_references_separate(self):
        expected = [ExpectedPayment("001", "Company", 100, 2), ExpectedPayment("pay", "Company", 100, 3)]
        actual = [ActualPayment("TX-1", "1", 100, 2), ActualPayment("TX-2", "PAY", 100, 3)]
        groups = group_payments_by_reference(expected, actual)
        self.assertEqual([g.payment_reference for g in groups], ["001", "pay", "1", "PAY"])

    def test_empty_inputs_produce_no_groups(self):
        self.assertEqual(group_payments_by_reference([], []), [])


if __name__ == "__main__":
    unittest.main()
