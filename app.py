"""Entry point for the local payment reconciliation interface."""

from pathlib import Path

import streamlit as st

from reconciliation.engine import reconcile_payments
from reconciliation.validation import (
    CSVValidationError,
    load_actual_payments,
    load_expected_payments,
)

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"

st.set_page_config(page_title="Payment Reconciliation Tool", layout="centered")

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
    st.session_state.pop("reconciliation_results", None)
    try:
        expected_payments = load_expected_payments(expected_file.getvalue(), expected_file.name)
        actual_payments = load_actual_payments(actual_file.getvalue(), actual_file.name)
        results = reconcile_payments(expected_payments, actual_payments)
    except CSVValidationError as error:
        st.error(str(error))
    else:
        st.session_state["reconciliation_results"] = results
        st.success(f"Comparison complete. {len(results)} payment references processed.")
