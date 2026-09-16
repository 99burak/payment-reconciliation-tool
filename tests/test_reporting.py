"""Check report contents, exact amounts, and CSV text escaping."""

import csv
from dataclasses import replace
from io import StringIO
from pathlib import Path
import unittest

from reconciliation.engine import reconcile_payments
from reconciliation.models import ReconciliationResult
from reconciliation.reporting import results_to_csv
from reconciliation.validation import load_actual_payments, load_expected_payments


def read_report(data):
    return list(csv.DictReader(StringIO(data.decode("utf-8-sig"), newline="")))


class ReportingTests(unittest.TestCase):
    def test_sample_report_matches_fixture_amounts_and_statuses(self):
        samples = Path(__file__).resolve().parents[1] / "samples"
        results = reconcile_payments(
            load_expected_payments((samples / "expected_payments.csv").read_bytes()),
            load_actual_payments((samples / "actual_payments.csv").read_bytes()),
        )
        original = results.copy()
        rows = read_report(results_to_csv(results))
        with (samples / "expected_results.csv").open(encoding="utf-8-sig", newline="") as handle:
            expected = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 8)
        for row, fixture, result in zip(rows, expected, results, strict=True):
            for field in ("payment_reference", "expected_amount", "actual_amount", "difference", "status"):
                self.assertEqual(row[field], fixture[field])
            self.assertEqual(row["description"], result.description)
        self.assertEqual(results, original)

    def test_exact_amounts_and_special_text_round_trip(self):
        result = ReconciliationResult(
            payment_reference='001-Ödeme,"A"\nB', status="amount_mismatch",
            expected_amount_cents=9007199254740993,
            actual_amount_cents=9007199254740992, difference_cents=-1,
            description='Difference, "quoted"\nİşlem açıklaması',
            expected_records=(), actual_records=(),
        )
        data = results_to_csv([result])
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        row = read_report(data)[0]
        self.assertEqual(row["payment_reference"], result.payment_reference)
        self.assertEqual(row["description"], result.description)
        self.assertEqual(row["expected_amount"], "90071992547409.93")
        self.assertEqual(row["actual_amount"], "90071992547409.92")
        self.assertEqual(row["difference"], "-0.01")
        positive = read_report(results_to_csv([replace(result, difference_cents=1)]))[0]
        self.assertEqual(positive["difference"], "0.01")

    def test_exports_only_supplied_results_in_supplied_order(self):
        results = reconcile_payments([], load_actual_payments(
            b"transaction_id,payment_reference,amount\nT1,001,10\nT2,002,20\nT3,003,30\n"
        ))
        rows = read_report(results_to_csv([results[2], results[0]]))
        self.assertEqual([row["payment_reference"] for row in rows], ["003", "001"])

    def test_empty_results_produce_only_the_header(self):
        data = results_to_csv([])
        self.assertEqual(read_report(data), [])
        self.assertEqual(data.decode("utf-8-sig").strip(),
                         "payment_reference,expected_amount,actual_amount,difference,status,description")


if __name__ == "__main__":
    unittest.main()
