"""In-memory payment records; these are not database tables."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedPayment:
    payment_reference: str
    customer_name: str
    amount_cents: int
    source_row: int


@dataclass(frozen=True)
class ActualPayment:
    transaction_id: str
    payment_reference: str
    amount_cents: int
    source_row: int


@dataclass(frozen=True)
class PaymentPair:
    """Two records sharing a unique reference, kept together for comparison."""

    expected: ExpectedPayment
    actual: ActualPayment


@dataclass(frozen=True)
class PaymentGroup:
    """All source records for one reference, preserved on their original side."""

    payment_reference: str
    expected_records: tuple[ExpectedPayment, ...]
    actual_records: tuple[ActualPayment, ...]

    @property
    def requires_review(self) -> bool:
        """A repeated reference on either side makes automatic pairing ambiguous."""
        return len(self.expected_records) > 1 or len(self.actual_records) > 1
