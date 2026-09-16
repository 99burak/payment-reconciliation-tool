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
                self.assertFalse(self.app.success)
                self.assertFalse(self.app.button(key="compare").disabled)

                self.app.button(key="compare").click().run()
                self.assertFalse(self.app.exception)
                result = next(r for r in self.app.session_state["reconciliation_results"]
                              if r.payment_reference == "PAY-001")
                self.assertEqual(result.status, "amount_mismatch")
                self.assertEqual(result.difference_cents, 10000 if index == 0 else -10000)

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

    def test_rerun_and_sample_download_do_not_discard_current_results(self):
        self.select_both_files()
        self.app.button(key="compare").click().run()
        results = self.app.session_state["reconciliation_results"]
        self.app.run()
        self.assertEqual(self.app.session_state["reconciliation_results"], results)
        for index in (0, 1):
            self.app.download_button[index].click().run()
            self.assertFalse(self.app.exception)
            self.assertEqual(self.app.session_state["reconciliation_results"], results)

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
