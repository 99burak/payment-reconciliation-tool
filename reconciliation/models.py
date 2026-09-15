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
