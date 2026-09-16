"""Smoke and interaction checks for the payment upload screen."""

from pathlib import Path
from collections import Counter
import unittest

from streamlit.testing.v1 import AppTest


PROJECT_DIR = Path(__file__).resolve().parents[1]


class UploadScreenTests(unittest.TestCase):
    def test_screen_starts_with_empty_uploads_and_sample_downloads(self):
        app = AppTest.from_file(str(PROJECT_DIR / "app.py"), default_timeout=10).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.file_uploader), 2)
        self.assertIsNone(app.session_state["expected_csv"])
        self.assertIsNone(app.session_state["actual_csv"])
        self.assertEqual(len(app.dataframe), 0)
        self.assertEqual(len(app.metric), 0)
        self.assertEqual(len(app.download_button), 2)
        for download in app.download_button:
            self.assertTrue(download.proto.url)
            self.assertFalse(download.disabled)

    def test_selecting_second_file_preserves_first_file_and_keeps_inputs_separate(self):
        app = AppTest.from_file(str(PROJECT_DIR / "app.py"), default_timeout=10).run()
        expected_bytes = (PROJECT_DIR / "samples" / "expected_payments.csv").read_bytes()
        actual_bytes = (PROJECT_DIR / "samples" / "actual_payments.csv").read_bytes()
        app.file_uploader[0].set_value(("expected.csv", expected_bytes, "text/csv")).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["expected_csv"].getvalue(), expected_bytes)
        self.assertIsNone(app.session_state["actual_csv"])

        app.file_uploader[1].set_value(("actual.csv", actual_bytes, "text/csv")).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["expected_csv"].name, "expected.csv")
        self.assertEqual(app.session_state["expected_csv"].getvalue(), expected_bytes)
        self.assertEqual(app.session_state["actual_csv"].name, "actual.csv")
        self.assertEqual(app.session_state["actual_csv"].getvalue(), actual_bytes)


class CompareScreenTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(PROJECT_DIR / "app.py"), default_timeout=10).run()
        self.expected_bytes = (PROJECT_DIR / "samples" / "expected_payments.csv").read_bytes()
        self.actual_bytes = (PROJECT_DIR / "samples" / "actual_payments.csv").read_bytes()

    def select_both_files(self):
        self.app.file_uploader[0].set_value(("expected.csv", self.expected_bytes, "text/csv"))
        self.app.file_uploader[1].set_value(("actual.csv", self.actual_bytes, "text/csv")).run()

    def test_compare_requires_both_files(self):
        self.assertTrue(self.app.button(key="compare").disabled)
        self.app.file_uploader[0].set_value(("expected.csv", self.expected_bytes, "text/csv")).run()
        self.assertTrue(self.app.button(key="compare").disabled)
        self.app.file_uploader[0].clear()
        self.app.file_uploader[1].set_value(("actual.csv", self.actual_bytes, "text/csv")).run()
        self.assertTrue(self.app.button(key="compare").disabled)
        self.app.file_uploader[0].set_value(("expected.csv", self.expected_bytes, "text/csv")).run()
        self.assertFalse(self.app.button(key="compare").disabled)
        self.assertNotIn("reconciliation_results", self.app.session_state)

    def test_compare_stores_complete_results_and_shows_success(self):
        self.select_both_files()
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        self.assertFalse(self.app.error)
        self.assertIn("8 payment references", self.app.success[0].value)
        results = self.app.session_state["reconciliation_results"]
        self.assertEqual(Counter(r.status for r in results), {
            "matched": 2, "amount_mismatch": 2, "missing": 1,
            "unexpected": 1, "review_required": 2,
        })
        self.assertEqual(sum(len(r.expected_records) + len(r.actual_records) for r in results), 16)

    def test_repeated_comparison_replaces_results_instead_of_appending(self):
        self.select_both_files()
        self.app.button(key="compare").click().run()
        first_results = self.app.session_state["reconciliation_results"]
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["reconciliation_results"], first_results)
        self.assertEqual(len(self.app.session_state["reconciliation_results"]), 8)

    def test_invalid_file_on_either_side_reports_source_and_clears_previous_results(self):
        for index, filename, invalid_data in [
            (0, "invalid_expected.csv", b"payment_reference,customer_name,amount\nP,Company,nope\n"),
            (1, "invalid_actual.csv", b"transaction_id,payment_reference,amount\nTX,P,nope\n"),
        ]:
            with self.subTest(filename=filename):
                self.select_both_files()
                self.app.button(key="compare").click().run()
                self.assertIn("reconciliation_results", self.app.session_state)
                self.app.file_uploader[index].set_value((filename, invalid_data, "text/csv")).run()
                self.app.button(key="compare").click().run()
                self.assertFalse(self.app.exception)
                self.assertIn(f"{filename}, row 2:", self.app.error[0].value)
                self.assertFalse(self.app.success)
                self.assertNotIn("reconciliation_results", self.app.session_state)

    def test_replacing_either_file_clears_results_even_with_the_same_filename(self):
        for index, filename, original_bytes in [
            (0, "expected.csv", self.expected_bytes),
            (1, "actual.csv", self.actual_bytes),
        ]:
            with self.subTest(index=index):
                self.select_both_files()
                self.app.button(key="compare").click().run()
                self.assertIn("reconciliation_results", self.app.session_state)
                changed_bytes = original_bytes.replace(b"1000.00", b"900.00", 1)
                self.app.file_uploader[index].set_value((filename, changed_bytes, "text/csv")).run()
                self.assertFalse(self.app.exception)
                self.assertNotIn("reconciliation_results", self.app.session_state)
                self.assertEqual(len(self.app.dataframe), 0)
                self.assertEqual(len(self.app.metric), 0)
                self.assertFalse(self.app.success)
                self.assertFalse(self.app.button(key="compare").disabled)

                self.app.button(key="compare").click().run()
                self.assertFalse(self.app.exception)
                result = next(r for r in self.app.session_state["reconciliation_results"]
                              if r.payment_reference == "PAY-001")
                self.assertEqual(result.status, "amount_mismatch")
                self.assertEqual(result.difference_cents, 10000 if index == 0 else -10000)
                self.assertEqual({m.label: m.value for m in self.app.metric}, {
                    "Matched": "1", "Amount mismatch": "3", "Missing": "1",
                    "Unexpected": "1", "Review required": "2",
                })

    def test_removing_either_file_clears_results_and_disables_comparison(self):
        for index in (0, 1):
            with self.subTest(index=index):
                self.select_both_files()
                self.app.button(key="compare").click().run()
                self.assertIn("reconciliation_results", self.app.session_state)
                self.app.file_uploader[index].clear().run()
                self.assertFalse(self.app.exception)
                self.assertNotIn("reconciliation_results", self.app.session_state)
                self.assertFalse(self.app.success)
                self.assertTrue(self.app.button(key="compare").disabled)
                self.assertIsNotNone(self.app.file_uploader[1 - index].value)
                self.assertEqual(len(self.app.dataframe), 0)
                self.assertEqual(len(self.app.metric), 0)

    def test_rerun_and_sample_download_do_not_discard_current_results(self):
        self.select_both_files()
        self.app.button(key="compare").click().run()
        results = self.app.session_state["reconciliation_results"]
        self.app.run()
        self.assertEqual(self.app.session_state["reconciliation_results"], results)
        self.assertEqual(len(self.app.dataframe[0].value), 8)
        for index in (0, 1):
            self.app.download_button[index].click().run()
            self.assertFalse(self.app.exception)
            self.assertEqual(self.app.session_state["reconciliation_results"], results)
            self.assertEqual(len(self.app.dataframe[0].value), 8)

    def test_summary_counts_all_five_statuses_and_survives_a_rerun(self):
        self.select_both_files()
        self.assertEqual(len(self.app.metric), 0)
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        expected_counts = {
            "Matched": "2", "Amount mismatch": "2", "Missing": "1",
            "Unexpected": "1", "Review required": "2",
        }
        self.assertEqual(len(self.app.metric), 5)
        self.assertEqual({m.label: m.value for m in self.app.metric}, expected_counts)
        self.assertEqual(sum(int(m.value) for m in self.app.metric), len(self.app.dataframe[0].value))
        self.app.run()
        self.assertEqual({m.label: m.value for m in self.app.metric}, expected_counts)

    def test_summary_counts_duplicate_reference_once_and_shows_zero_for_absent_statuses(self):
        expected = b"payment_reference,customer_name,amount\nP,Company,100\n"
        actual = b"transaction_id,payment_reference,amount\nTX-1,P,100\nTX-2,P,100\nTX-3,P,100\n"
        self.app.file_uploader[0].set_value(("expected.csv", expected, "text/csv"))
        self.app.file_uploader[1].set_value(("actual.csv", actual, "text/csv")).run()
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual({m.label: m.value for m in self.app.metric}, {
            "Matched": "0", "Amount mismatch": "0", "Missing": "0",
            "Unexpected": "0", "Review required": "1",
        })

    def test_results_table_displays_all_references_statuses_and_amounts(self):
        self.select_both_files()
        self.assertEqual(len(self.app.dataframe), 0)
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.dataframe), 1)
        table = self.app.dataframe[0].value
        self.assertEqual(list(table.columns), [
            "Reference", "Expected (TRY)", "Actual (TRY)", "Difference (TRY)", "Status", "Description",
        ])
        self.assertEqual(
            table.drop(columns="Description").values.tolist(),
            [
                ["PAY-001", "1,000.00", "1,000.00", "0.00", "matched"],
                ["PAY-002", "2,500.00", "2,300.00", "-200.00", "amount_mismatch"],
                ["PAY-003", "750.00", "", "", "missing"],
                ["PAY-004", "", "", "", "review_required"],
                ["PAY-005", "100.00", "125.00", "25.00", "amount_mismatch"],
                ["PAY-006", "1,250.75", "1,250.75", "0.00", "matched"],
                ["PAY-007", "", "", "", "review_required"],
                ["PAY-099", "", "400.00", "", "unexpected"],
            ],
        )
        self.assertEqual(table["Description"].tolist(),
                         [r.description for r in self.app.session_state["reconciliation_results"]])

    def test_table_keeps_large_amounts_and_negative_one_cent_exact(self):
        expected = b"payment_reference,customer_name,amount\n001,Company,90071992547409.93\n"
        actual = b"transaction_id,payment_reference,amount\nTX-1,001,90071992547409.92\n"
        self.app.file_uploader[0].set_value(("expected.csv", expected, "text/csv"))
        self.app.file_uploader[1].set_value(("actual.csv", actual, "text/csv")).run()
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        row = self.app.dataframe[0].value.iloc[0]
        self.assertEqual(row["Reference"], "001")
        self.assertEqual(row["Expected (TRY)"], "90,071,992,547,409.93")
        self.assertEqual(row["Actual (TRY)"], "90,071,992,547,409.92")
        self.assertEqual(row["Difference (TRY)"], "-0.01")

    def test_empty_uploaded_file_is_validated_and_reported(self):
        self.select_both_files()
        self.app.file_uploader[0].set_value(("empty.csv", b"", "text/csv")).run()
        self.assertFalse(self.app.button(key="compare").disabled)
        self.app.button(key="compare").click().run()
        self.assertFalse(self.app.exception)
        self.assertIn("empty.csv: File is empty.", self.app.error[0].value)
        self.assertNotIn("reconciliation_results", self.app.session_state)


if __name__ == "__main__":
    unittest.main()
