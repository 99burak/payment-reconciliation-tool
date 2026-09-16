"""Entry point for the local payment reconciliation interface."""

from collections import Counter
from pathlib import Path

import streamlit as st

from reconciliation.engine import reconcile_payments
from reconciliation.validation import (
    CSVValidationError,
    load_actual_payments,
    load_expected_payments,
)

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"


def clear_comparison_results() -> None:
    """Discard results when an input changes or a new comparison starts."""
    st.session_state.pop("reconciliation_results", None)
    for key in ("reference_search", "status_filter", "issues_only"):
        st.session_state.pop(key, None)


def format_amount(cents: int | None) -> str:
    """Display TRY amounts without rounding or converting missing values to zero."""
    if cents is None:
        return ""
    whole, fraction = divmod(abs(cents), 100)
    sign = "-" if cents < 0 else ""
    return f"{sign}{whole:,}.{fraction:02d}"


st.set_page_config(page_title="Payment Reconciliation Tool", layout="wide")

st.title("Payment Reconciliation Tool")
st.write("Compare expected payments with actual payments and investigate differences.")

st.caption(
    "Use comma-separated UTF-8 CSV files. Amounts must be positive TRY values "
    "with a dot decimal separator, such as 1250.75."
)

expected_column, actual_column = st.columns(2)

with expected_column:
    st.subheader("Expected payments")
    st.caption("Payments you expect to receive.")
    st.markdown("Required columns: `payment_reference`, `customer_name`, `amount`.")
    expected_file = st.file_uploader(
        "Upload expected payments CSV",
        type=["csv"],
        accept_multiple_files=False,
        max_upload_size=5,
        key="expected_csv",
        on_change=clear_comparison_results,
    )
    st.download_button(
        "Download expected sample",
        data=(SAMPLES_DIR / "expected_payments.csv").read_bytes(),
        file_name="expected_payments.csv",
        mime="text/csv",
        on_click="ignore",
        key="download_expected_sample",
    )

with actual_column:
    st.subheader("Actual payments")
    st.caption("Payments that were actually received.")
    st.markdown("Required columns: `transaction_id`, `payment_reference`, `amount`.")
    actual_file = st.file_uploader(
        "Upload actual payments CSV",
        type=["csv"],
        accept_multiple_files=False,
        max_upload_size=5,
        key="actual_csv",
        on_change=clear_comparison_results,
    )
    st.download_button(
        "Download actual sample",
        data=(SAMPLES_DIR / "actual_payments.csv").read_bytes(),
        file_name="actual_payments.csv",
        mime="text/csv",
        on_click="ignore",
        key="download_actual_sample",
    )

st.caption("Maximum 5 MiB and 10,000 payment rows per file. Samples contain fictional data.")
files_ready = expected_file is not None and actual_file is not None
compare_clicked = st.button("Compare", disabled=not files_ready, type="primary", key="compare")

if not files_ready:
    st.info("Select both CSV files to compare payments.")

if compare_clicked and files_ready:
    # A failed attempt must not leave a previous successful result behind.
    clear_comparison_results()
    try:
        expected_payments = load_expected_payments(expected_file.getvalue(), expected_file.name)
        actual_payments = load_actual_payments(actual_file.getvalue(), actual_file.name)
        results = reconcile_payments(expected_payments, actual_payments)
    except CSVValidationError as error:
        st.error(str(error))
    else:
        st.session_state["reconciliation_results"] = results
        st.success(f"Comparison complete. {len(results)} payment references processed.")

if "reconciliation_results" in st.session_state:
    st.subheader("Reconciliation results")
    status_counts = Counter(result.status for result in st.session_state["reconciliation_results"])
    status_labels = {
        "matched": "Matched",
        "amount_mismatch": "Amount mismatch",
        "missing": "Missing",
        "unexpected": "Unexpected",
        "review_required": "Review required",
    }
    st.caption("Counts represent payment reference groups, not individual source rows.")
    for column, (status, label) in zip(st.columns(5), status_labels.items(), strict=True):
        column.metric(label, status_counts[status])

    search_column, status_column, issues_column = st.columns(3)
    reference_search = search_column.text_input(
        "Search payment reference", key="reference_search",
        help="Find references containing this text, ignoring letter case.",
    ).strip().casefold()
    selected_status = status_column.selectbox(
        "Status", options=["all", *status_labels],
        format_func=lambda status: "All statuses" if status == "all" else status_labels[status],
        key="status_filter",
    )
    issues_only = issues_column.checkbox("Show issues only", key="issues_only")
    filtered_results = [
        result for result in st.session_state["reconciliation_results"]
        if reference_search in result.payment_reference.casefold()
        and (selected_status == "all" or result.status == selected_status)
        and (not issues_only or result.status != "matched")
    ]
    st.caption(
        f"Showing {len(filtered_results)} of "
        f"{len(st.session_state['reconciliation_results'])} payment references. "
        "Summary counts above include all results."
    )
    st.caption("Amounts are in TRY. Blank cells mean the amount or difference cannot be determined.")
    rows = [
        {
            "Reference": result.payment_reference,
            "Expected (TRY)": format_amount(result.expected_amount_cents),
            "Actual (TRY)": format_amount(result.actual_amount_cents),
            "Difference (TRY)": format_amount(result.difference_cents),
            "Status": result.status,
            "Description": result.description,
        }
        for result in filtered_results
    ]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch", key="results_table")
    else:
        st.info("No results match the selected filters.")
