"""Reference pairing checks; amount comparison belongs to the next step."""

from pathlib import Path
import unittest

from reconciliation.engine import match_unique_payments
from reconciliation.models import ActualPayment, ExpectedPayment
from reconciliation.validation import load_actual_payments, load_expected_payments


def expected(reference: str, cents: int = 100) -> ExpectedPayment:
    return ExpectedPayment(reference, "Sample Company", cents, 2)


def actual(reference: str, cents: int = 100, transaction: str = "TX-1") -> ActualPayment:
    return ActualPayment(transaction, reference, cents, 2)


class ReferenceMatchingTests(unittest.TestCase):
    def test_pairs_by_reference_instead_of_input_position(self):
        expected_records = [expected("P-1"), expected("P-2")]
        actual_records = [actual("P-2", transaction="TX-2"), actual("P-1")]
        pairs = match_unique_payments(expected_records, actual_records)
        self.assertEqual(
            [(p.expected.payment_reference, p.actual.transaction_id) for p in pairs],
            [("P-1", "TX-1"), ("P-2", "TX-2")],
        )

    def test_pairs_different_amounts_without_comparing_them(self):
        pairs = match_unique_payments([expected("P-1", 250000)], [actual("P-1", 230000)])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].expected.amount_cents, 250000)
        self.assertEqual(pairs[0].actual.amount_cents, 230000)

    def test_equal_amounts_do_not_pair_different_references(self):
        self.assertEqual(match_unique_payments([expected("P-1")], [actual("P-2")]), [])

    def test_duplicate_references_never_select_an_arbitrary_payment(self):
        for expected_records, actual_records in [
            ([expected("P")], [actual("P"), actual("P", transaction="TX-2")]),
            ([expected("P"), expected("P")], [actual("P")]),
            ([expected("P"), expected("P")], [actual("P"), actual("P", transaction="TX-2")]),
        ]:
            with self.subTest(expected_count=len(expected_records), actual_count=len(actual_records)):
                self.assertEqual(match_unique_payments(expected_records, actual_records), [])

    def test_empty_inputs_have_no_pairs(self):
        for expected_records, actual_records in [([], []), ([expected("P")], []), ([], [actual("P")])]:
            with self.subTest(expected_records=expected_records, actual_records=actual_records):
                self.assertEqual(match_unique_payments(expected_records, actual_records), [])

    def test_reference_case_and_leading_zeros_remain_significant(self):
        self.assertEqual(
            match_unique_payments([expected("001"), expected("pay-1")], [actual("1"), actual("PAY-1")]),
            [],
        )

    def test_preserves_inputs_and_original_records(self):
        expected_records = [expected("P"), expected("missing")]
        actual_records = [actual("unexpected"), actual("P", transaction="TX-2")]
        original_expected, original_actual = expected_records.copy(), actual_records.copy()
        pairs = match_unique_payments(expected_records, actual_records)
        self.assertEqual(expected_records, original_expected)
        self.assertEqual(actual_records, original_actual)
        self.assertIs(pairs[0].expected, expected_records[0])
        self.assertIs(pairs[0].actual, actual_records[1])

    def test_sample_files_produce_four_unambiguous_pairs(self):
        samples = Path(__file__).resolve().parents[1] / "samples"
        expected_records = load_expected_payments((samples / "expected_payments.csv").read_bytes())
        actual_records = load_actual_payments((samples / "actual_payments.csv").read_bytes())
        pairs = match_unique_payments(expected_records, actual_records)
        self.assertEqual([p.expected.payment_reference for p in pairs], ["PAY-001", "PAY-002", "PAY-005", "PAY-006"])
        self.assertEqual((len(expected_records), len(actual_records)), (8, 8))


if __name__ == "__main__":
    unittest.main()
