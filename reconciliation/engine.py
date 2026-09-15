"""Pair validated payment records and check whether their amounts agree."""

from collections import Counter

from reconciliation.models import ActualPayment, ExpectedPayment, PaymentPair


def match_unique_payments(
    expected_payments: list[ExpectedPayment],
    actual_payments: list[ActualPayment],
) -> list[PaymentPair]:
    """Pair references appearing exactly once in each input, in expected order.

    This is only the pairing step, not a complete reconciliation report.
    Missing and duplicate references are excluded from pairs; the original
    inputs remain unchanged for their classification in a later stage.
    Amounts do not affect whether two records are paired.
    """
    expected_counts = Counter(payment.payment_reference for payment in expected_payments)
    actual_by_reference: dict[str, list[ActualPayment]] = {}
    for payment in actual_payments:
        actual_by_reference.setdefault(payment.payment_reference, []).append(payment)

    pairs = []
    for expected in expected_payments:
        actual_records = actual_by_reference.get(expected.payment_reference, [])
        if expected_counts[expected.payment_reference] == 1 and len(actual_records) == 1:
            pairs.append(PaymentPair(expected=expected, actual=actual_records[0]))
    return pairs


def amounts_match(pair: PaymentPair) -> bool:
    """Check exact cent equality for a pair produced by match_unique_payments."""
    return pair.expected.amount_cents == pair.actual.amount_cents
