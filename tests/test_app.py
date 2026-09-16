"""Smoke and interaction checks for the payment upload screen."""

from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
