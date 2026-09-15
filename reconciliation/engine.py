"""Reconcile validated payments while preserving every source record."""

from reconciliation.models import (
    ActualPayment,
    ExpectedPayment,
    PaymentGroup,
    PaymentPair,
    ReconciliationResult,
)


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
    Missing and duplicate references are excluded from pairs; use
    reconcile_payments for a complete result list. Inputs remain unchanged.
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


def reconcile_payments(
    expected_payments: list[ExpectedPayment],
    actual_payments: list[ActualPayment],
) -> list[ReconciliationResult]:
    """Return one result per reference, prioritizing duplicates over other states.

    Missing amounts and uncomputable differences are None, not zero. Duplicate
    groups have no summary amounts; inspect their preserved source records.
    """
    results = []
    for group in group_payments_by_reference(expected_payments, actual_payments):
        expected_amount = None
        actual_amount = None
        difference = None

        if group.requires_review:
            status = "review_required"
            duplicate_sides = []
            if len(group.expected_records) > 1:
                duplicate_sides.append("expected payments")
            if len(group.actual_records) > 1:
                duplicate_sides.append("actual payments")
            description = (
                f"Duplicate reference in {' and '.join(duplicate_sides)}; manual review required."
            )
        elif not group.actual_records:
            status = "missing"
            expected_amount = group.expected_records[0].amount_cents
            description = "No actual payment was found for this reference."
        elif not group.expected_records:
            status = "unexpected"
            actual_amount = group.actual_records[0].amount_cents
            description = "No expected payment was found for this reference."
        else:
            pair = PaymentPair(group.expected_records[0], group.actual_records[0])
            expected_amount = pair.expected.amount_cents
            actual_amount = pair.actual.amount_cents
            status = get_payment_status(pair)
            difference = calculate_difference_cents(pair)
            if status == "matched":
                description = "Reference and amount match."
            else:
                whole, cents = divmod(abs(difference), 100)
                direction = "below" if difference < 0 else "above"
                description = (
                    f"Actual payment is {whole}.{cents:02d} TRY {direction} the expected amount."
                )

        results.append(
            ReconciliationResult(
                payment_reference=group.payment_reference,
                status=status,
                expected_amount_cents=expected_amount,
                actual_amount_cents=actual_amount,
                difference_cents=difference,
                description=description,
                expected_records=group.expected_records,
                actual_records=group.actual_records,
            )
        )
    return results
