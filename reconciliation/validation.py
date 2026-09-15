"""Read payment CSV bytes and reject invalid input before reconciliation."""

import csv
import io
import re
from collections.abc import Iterator

from reconciliation.models import ActualPayment, ExpectedPayment


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_DATA_ROWS = 10_000
EXPECTED_COLUMNS = ("payment_reference", "customer_name", "amount")
ACTUAL_COLUMNS = ("transaction_id", "payment_reference", "amount")


class CSVValidationError(ValueError):
    """An input error with a filename and optional physical source line."""

    def __init__(self, filename: str, message: str, row: int | None = None):
        self.filename = filename
        self.row = row
        location = f"{filename}, row {row}" if row is not None else filename
        super().__init__(f"{location}: {message}")


def _amount_in_cents(value: str, filename: str, row: int) -> int:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", value):
        raise CSVValidationError(
            filename,
            "Amount must be a positive number with a dot separator and at most "
            "two decimal places (for example, 1250.75).",
            row,
        )

    # Pad the fractional part instead of using floating-point arithmetic.
    whole, _, fraction = value.partition(".")
    try:
        amount_cents = int(whole + fraction.ljust(2, "0"))
    except ValueError as exc:
        raise CSVValidationError(filename, "Amount is too large to process.", row) from exc
    if amount_cents <= 0:
        raise CSVValidationError(filename, "Amount must be greater than zero.", row)
    return amount_cents


def _read_rows(
    data: bytes, filename: str, required_columns: tuple[str, ...]
) -> Iterator[tuple[int, dict[str, str]]]:
    if len(data) > MAX_FILE_BYTES:
        raise CSVValidationError(filename, "File exceeds the 5 MiB size limit.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVValidationError(filename, "File must use UTF-8 encoding.") from exc

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    row_number = 1
    count = 0
    try:
        header = next(reader, None)
        if header is None:
            raise CSVValidationError(filename, "File is empty.")
        header = [column.strip() for column in header]
        if not header or any(not column for column in header):
            raise CSVValidationError(filename, "Header contains an empty column name.", 1)
        if len(set(header)) != len(header):
            raise CSVValidationError(filename, "Header contains duplicate column names.", 1)
        missing = [column for column in required_columns if column not in header]
        if missing:
            raise CSVValidationError(
                filename, f"Missing required columns: {', '.join(missing)}.", 1
            )

        while True:
            # A quoted field may span several physical lines.
            row_number = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not values or all(not value.strip() for value in values):
                continue
            if len(values) != len(header):
                raise CSVValidationError(
                    filename,
                    f"Expected {len(header)} fields but found {len(values)}.",
                    row_number,
                )
            count += 1
            if count > MAX_DATA_ROWS:
                raise CSVValidationError(
                    filename, "File exceeds the 10,000 payment row limit.", row_number
                )
            row = dict(zip(header, (value.strip() for value in values), strict=True))
            for column in required_columns:
                if not row[column]:
                    raise CSVValidationError(
                        filename, f"Required field '{column}' is empty.", row_number
                    )
            yield row_number, row
    except csv.Error as exc:
        raise CSVValidationError(filename, f"Malformed CSV: {exc}.", row_number) from exc

    if count == 0:
        raise CSVValidationError(filename, "File contains no payment rows.")


def load_expected_payments(
    data: bytes, filename: str = "expected_payments.csv"
) -> list[ExpectedPayment]:
    """Return all expected records, or raise an error without partial results."""
    return [
        ExpectedPayment(
            payment_reference=row["payment_reference"],
            customer_name=row["customer_name"],
            amount_cents=_amount_in_cents(row["amount"], filename, source_row),
            source_row=source_row,
        )
        for source_row, row in _read_rows(data, filename, EXPECTED_COLUMNS)
    ]


def load_actual_payments(
    data: bytes, filename: str = "actual_payments.csv"
) -> list[ActualPayment]:
    """Return actual records with unique transaction IDs; preserve references."""
    payments = []
    transaction_rows: dict[str, int] = {}
    for source_row, row in _read_rows(data, filename, ACTUAL_COLUMNS):
        transaction_id = row["transaction_id"]
        if transaction_id in transaction_rows:
            raise CSVValidationError(
                filename,
                f"Duplicate transaction_id; first seen on row {transaction_rows[transaction_id]}.",
                source_row,
            )
        transaction_rows[transaction_id] = source_row
        payments.append(
            ActualPayment(
                transaction_id=transaction_id,
                payment_reference=row["payment_reference"],
                amount_cents=_amount_in_cents(row["amount"], filename, source_row),
                source_row=source_row,
            )
        )
    return payments
