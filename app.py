"""Entry point for the local payment reconciliation interface."""

import streamlit as st


st.set_page_config(page_title="Payment Reconciliation Tool", layout="centered")

st.title("Payment Reconciliation Tool")
st.write("Compare expected payments with actual payments and investigate differences.")

st.info(
    "The project skeleton is ready. File uploads and payment comparison "
    "will be added in the following development stages."
)

st.subheader("Planned workflow")
st.markdown(
    "1. Upload expected and actual payment CSV files.\n"
    "2. Compare payments by reference and amount.\n"
    "3. Review differences and download a report."
)

st.caption("First version: local use, TRY amounts, and no account required.")
