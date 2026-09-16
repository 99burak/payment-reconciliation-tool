"""Convert reconciliation results into a downloadable CSV report."""

import csv
from collections.abc import Iterable
from io import StringIO

from reconciliation.models import ReconciliationResult


def _format_amount(cents: int | None) -> str:
    """Keep missing values blank and format integer cents without rounding."""
    if cents is None:
        return ""
    whole, fraction = divmod(abs(cents), 100)
    sign = "-" if cents < 0 else ""
    return f"{sign}{whole}.{fraction:02d}"


def results_to_csv(results: Iterable[ReconciliationResult]) -> bytes:
    """Export the supplied results in order, with a UTF-8 BOM for Excel."""
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "payment_reference", "expected_amount", "actual_amount",
        "difference", "status", "description",
    ])
    for result in results:
        writer.writerow([
            result.payment_reference,
            _format_amount(result.expected_amount_cents),
            _format_amount(result.actual_amount_cents),
            _format_amount(result.difference_cents),
            result.status,
            result.description,
        ])
    return output.getvalue().encode("utf-8-sig")
