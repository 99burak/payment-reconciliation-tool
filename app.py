"""Entry point for the local payment reconciliation interface."""

from pathlib import Path

import streamlit as st


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
st.info("File selection is available. Validation and comparison are not available on this screen yet.")
