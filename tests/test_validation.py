"""Behavior checks for payment CSV input, independent of the interface."""

import csv
import io
from pathlib import Path
import unittest

from reconciliation.validation import (
    CSVValidationError,
    MAX_FILE_BYTES,
    load_actual_payments,
    load_expected_payments,
)


SAMPLES = Path(__file__).resolve().parents[1] / "samples"
EXPECTED_HEADER = "payment_reference,customer_name,amount\n"
ACTUAL_HEADER = "transaction_id,payment_reference,amount\n"


def expected_csv(amount: str) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["payment_reference", "customer_name", "amount"])
    writer.writerow(["PAY-001", "Sample Company", amount])
    return output.getvalue().encode("utf-8")


class PaymentCSVTests(unittest.TestCase):
    def test_loads_sample_expected_payments(self):
        payments = load_expected_payments((SAMPLES / "expected_payments.csv").read_bytes())
        self.assertEqual(len(payments), 8)
        self.assertEqual(payments[5].amount_cents, 125075)
        self.assertEqual(payments[5].source_row, 7)
        self.assertEqual(payments[6].payment_reference, payments[7].payment_reference)

    def test_loads_sample_actual_payments_without_dropping_duplicate_references(self):
        payments = load_actual_payments((SAMPLES / "actual_payments.csv").read_bytes())
        self.assertEqual(len(payments), 8)
        self.assertEqual(payments[2].payment_reference, payments[3].payment_reference)
        self.assertNotEqual(payments[2].transaction_id, payments[3].transaction_id)
        self.assertEqual(payments[-1].amount_cents, 40000)

    def test_converts_supported_amounts_exactly(self):
        for amount, cents in [("1", 100), ("1.2", 120), ("0.01", 1),
                              ("0.10", 10), ("1250.75", 125075),
                              ("90071992547409.93", 9007199254740993)]:
            with self.subTest(amount=amount):
                self.assertEqual(load_expected_payments(expected_csv(amount))[0].amount_cents, cents)

    def test_rejects_invalid_amounts_without_rounding(self):
        for amount in ["0", "0.00", "-1", "+1", "1.234", "1.000", "1e2",
                       "NaN", "Infinity", "1,000.00", "10,50", "TRY 10", ".50",
                       "1.", "abc", "١٠.٠٠"]:
            with self.subTest(amount=amount):
                with self.assertRaises(CSVValidationError) as caught:
                    load_expected_payments(expected_csv(amount), "payments.csv")
                self.assertEqual(caught.exception.row, 2)
                self.assertIn("payments.csv", str(caught.exception))

    def test_oversized_integer_reports_a_validation_error(self):
        with self.assertRaisesRegex(CSVValidationError, "too large"):
            load_expected_payments(expected_csv("9" * 5000))

    def test_trims_fields_and_preserves_reference_case_and_leading_zeros(self):
        data = (EXPECTED_HEADER + " 000abc , Sample Company , 10.5 \n").encode()
        record = load_expected_payments(data)[0]
        self.assertEqual(record.payment_reference, "000abc")
        self.assertEqual(record.customer_name, "Sample Company")
        self.assertEqual(record.amount_cents, 1050)

    def test_accepts_utf8_bom_and_non_ascii_customer_names(self):
        data = (EXPECTED_HEADER + "PAY-001,Caf\u00e9 Company,1.00\n").encode("utf-8-sig")
        self.assertEqual(load_expected_payments(data)[0].customer_name, "Caf\u00e9 Company")

    def test_accepts_reordered_columns_and_ignores_extra_columns(self):
        data = b"note, amount ,customer_name,payment_reference\nignored,10.50,Sample Company,001\n"
        record = load_expected_payments(data)[0]
        self.assertEqual((record.payment_reference, record.amount_cents), ("001", 1050))

    def test_handles_quoted_commas_quotes_and_multiline_fields(self):
        data = (EXPECTED_HEADER + 'PAY-001,"Sample, ""North""\nCompany",10.00\n'
                'PAY-002,Other Company,20.00\n').encode()
        records = load_expected_payments(data)
        self.assertEqual(records[0].customer_name, 'Sample, "North"\nCompany')
        self.assertEqual([r.source_row for r in records], [2, 4])

    def test_blank_rows_are_skipped_without_changing_source_line_numbers(self):
        data = (EXPECTED_HEADER + "\n , , \nPAY-001,Sample Company,1\n").encode()
        records = load_expected_payments(data)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_row, 4)

    def test_rejects_empty_files_and_files_without_payments(self):
        for data in [b"", b"\xef\xbb\xbf", b"\n", EXPECTED_HEADER.encode(),
                     (EXPECTED_HEADER + "\n,,\n").encode()]:
            with self.subTest(data=data):
                with self.assertRaises(CSVValidationError):
                    load_expected_payments(data)

    def test_rejects_invalid_encoding(self):
        with self.assertRaisesRegex(CSVValidationError, "UTF-8"):
            load_expected_payments(EXPECTED_HEADER.encode() + b"P,Caf\xe9,1\n")

    def test_rejects_missing_columns_for_both_input_types(self):
        for loader, data, missing in [
            (load_expected_payments, b"payment_reference,amount\nP,1\n", "customer_name"),
            (load_actual_payments, b"payment_reference,amount\nP,1\n", "transaction_id"),
        ]:
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(CSVValidationError, missing) as caught:
                    loader(data)
                self.assertEqual(caught.exception.row, 1)

    def test_rejects_duplicate_or_empty_header_names(self):
        for header in ["payment_reference,customer_name,amount, amount",
                       "payment_reference,customer_name,amount,"]:
            with self.subTest(header=header):
                with self.assertRaises(CSVValidationError) as caught:
                    load_expected_payments((header + "\nP,C,1,x\n").encode())
                self.assertEqual(caught.exception.row, 1)

    def test_rejects_empty_required_fields(self):
        for loader, header in [(load_expected_payments, EXPECTED_HEADER),
                               (load_actual_payments, ACTUAL_HEADER)]:
            for index in range(3):
                values = ["ID", "Name", "1"]
                values[index] = " "
                with self.subTest(loader=loader.__name__, index=index):
                    with self.assertRaisesRegex(CSVValidationError, "is empty"):
                        loader((header + ",".join(values) + "\n").encode())

    def test_rejects_wrong_field_counts(self):
        for row in ["PAY-001,Company", "PAY-001,Company,1,extra"]:
            with self.subTest(row=row):
                with self.assertRaisesRegex(CSVValidationError, "fields") as caught:
                    load_expected_payments((EXPECTED_HEADER + row).encode())
                self.assertEqual(caught.exception.row, 2)

    def test_rejects_semicolon_delimited_input(self):
        with self.assertRaisesRegex(CSVValidationError, "Missing required columns"):
            load_expected_payments(b"payment_reference;customer_name;amount\nP;C;1\n")

    def test_rejects_malformed_quoted_input(self):
        with self.assertRaisesRegex(CSVValidationError, "Malformed CSV") as caught:
            load_expected_payments((EXPECTED_HEADER + 'P,"Unclosed name,1\n').encode())
        self.assertEqual(caught.exception.row, 2)

    def test_reports_line_after_a_multiline_record(self):
        data = (EXPECTED_HEADER + 'P,"Line one\nLine two",1\nQ,Company,invalid\n').encode()
        with self.assertRaises(CSVValidationError) as caught:
            load_expected_payments(data, "custom.csv")
        self.assertEqual(str(caught.exception).split(":")[0], "custom.csv, row 4")

    def test_rejects_duplicate_transaction_ids_after_trimming(self):
        data = (ACTUAL_HEADER + "TX-1,PAY-1,1\n TX-1 ,PAY-2,2\n").encode()
        with self.assertRaisesRegex(CSVValidationError, "first seen on row 2") as caught:
            load_actual_payments(data)
        self.assertEqual(caught.exception.row, 3)

    def test_late_invalid_record_fails_instead_of_returning_partial_results(self):
        data = (ACTUAL_HEADER + "TX-1,PAY-1,1\nTX-2,PAY-2,invalid\n").encode()
        with self.assertRaises(CSVValidationError):
            load_actual_payments(data)

    def test_enforces_file_size_limit(self):
        with self.assertRaisesRegex(CSVValidationError, "size limit"):
            load_expected_payments(b" " * (MAX_FILE_BYTES + 1))

    def test_accepts_exactly_the_file_size_limit(self):
        base = (EXPECTED_HEADER + "PAY-001,Company,1\n").encode()
        data = base + b"\n" * (MAX_FILE_BYTES - len(base))
        self.assertEqual(len(load_expected_payments(data)), 1)

    def test_accepts_ten_thousand_rows_and_rejects_one_more(self):
        rows = "".join(f"TX-{i},PAY-{i},1\n" for i in range(10_000))
        data = (ACTUAL_HEADER + rows).encode()
        self.assertEqual(len(load_actual_payments(data)), 10_000)
        with self.assertRaisesRegex(CSVValidationError, "row limit") as caught:
            load_actual_payments(data + b"TX-extra,PAY-extra,1\n")
        self.assertEqual(caught.exception.row, 10_002)


if __name__ == "__main__":
    unittest.main()
