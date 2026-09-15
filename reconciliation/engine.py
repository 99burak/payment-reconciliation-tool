"""Group validated payments, compare unique pairs, and identify duplicate references."""

from reconciliation.models import ActualPayment, ExpectedPayment, PaymentGroup, PaymentPair


def group_payments_by_reference(
    expected_payments: list[ExpectedPayment],
    actual_payments: list[ActualPayment],
) -> list[PaymentGroup]:
    """Preserve every record in one group per exact reference, without summing.

    Order follows first appearance in expected payments, then references only
    present in actual payments. Source records retain their order within a group.
    """
    expected_by_reference: dict[str, list[ExpectedPayment]] = {}
    actual_by_reference: dict[str, list[ActualPayment]] = {}
    for payment in expected_payments:
        expected_by_reference.setdefault(payment.payment_reference, []).append(payment)
    for payment in actual_payments:
        actual_by_reference.setdefault(payment.payment_reference, []).append(payment)

    references = dict.fromkeys([*expected_by_reference, *actual_by_reference])
    return [
        PaymentGroup(
            payment_reference=reference,
            expected_records=tuple(expected_by_reference.get(reference, [])),
            actual_records=tuple(actual_by_reference.get(reference, [])),
        )
        for reference in references
    ]


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
    return [
        PaymentPair(expected=group.expected_records[0], actual=group.actual_records[0])
        for group in group_payments_by_reference(expected_payments, actual_payments)
        if not group.requires_review and group.expected_records and group.actual_records
    ]


def amounts_match(pair: PaymentPair) -> bool:
    """Check exact cent equality for a pair produced by match_unique_payments."""
    return pair.expected.amount_cents == pair.actual.amount_cents


def get_payment_status(pair: PaymentPair) -> str:
    """Classify a unique reference pair by exact amount equality."""
    return "matched" if amounts_match(pair) else "amount_mismatch"


def calculate_difference_cents(pair: PaymentPair) -> int:
    """Return actual minus expected in cents: negative means underpayment."""
    return pair.actual.amount_cents - pair.expected.amount_cents
