# Payment Reconciliation Tool

A local Python and Streamlit application that compares expected payments with actual receipts from two CSV files. It matches payment references, identifies amount differences and missing payments, and exports a report for review.

## Features

- Validate CSV files with clear filename and row-level errors.
- Classify each reference as matched, amount mismatch, missing, unexpected, or requiring review.
- Compare amounts exactly using integer kuruş (one hundredth of a TRY), without floating-point rounding.
- View summary counts and a results table with explanations.
- Search references, filter by status, and show only issues.
- Download the filtered results as a CSV report.
- Try the workflow with included fictional sample data.

## Technology

Python 3.12, Streamlit 1.63.0, and Python's standard library (`csv`, `dataclasses`, `unittest`). UI interaction tests use Streamlit AppTest. No database or API service is required.

## Setup and run

Install Python 3.12 and Git first. Run the following in Windows PowerShell:

```powershell
git clone https://github.com/99burak/payment-reconciliation-tool.git
cd payment-reconciliation-tool
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open [the local application](http://127.0.0.1:8501/). Keep the terminal running; press `Ctrl+C` to stop the server. These commands use the virtual environment directly, so activation is unnecessary.

For subsequent runs, open PowerShell in the project folder and run only the final command. If an existing environment reports `No module named pip`, run `.\.venv\Scripts\python.exe -m ensurepip --upgrade` before installing requirements.

On macOS or Linux, create the environment with `python3.12 -m venv .venv` and use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.

## CSV input format

Use UTF-8 files (with or without a BOM), comma separators, and the exact column names below. Column order may vary; additional columns are ignored. Required fields must not be empty. Surrounding whitespace is trimmed and blank rows are skipped.

**Expected payments** describe what should have been received:

```csv
payment_reference,customer_name,amount
PAY-001,Northwind Supplies,1000.00
PAY-002,Blue Harbor Services,2500.00
```

**Actual payments** describe receipts that occurred:

```csv
transaction_id,payment_reference,amount
TX-101,PAY-001,1000.00
TX-102,PAY-002,2300.00
```

`payment_reference` connects the two files. `transaction_id` identifies an actual transaction and must be unique within its file. Repeated payment references are accepted but require manual review.

Amounts must be positive TRY values with at most two decimal places: `100`, `100.5`, and `100.50` are accepted. Currency symbols, thousands separators, decimal commas, zero, and negative input amounts are rejected. Each file is limited to **5 MiB and 10,000 payment rows**. An invalid file is rejected entirely rather than partially processed.

## Matching rules

References are matched exactly after trimming whitespace. Matching is case-sensitive and preserves leading zeros: `001` and `1` are different references. Reference search in the interface is case-insensitive and supports partial text.

| Status | Meaning |
| --- | --- |
| `matched` | One record on each side, with equal amounts. |
| `amount_mismatch` | One record on each side, with different amounts. |
| `missing` | An expected payment has no actual payment. |
| `unexpected` | An actual payment has no expected payment. |
| `review_required` | A reference occurs more than once on either side. |

Duplicate references take priority over other classifications. Their amounts are not summed or automatically paired, even if totals happen to agree.

For one-to-one matches, **difference = actual amount − expected amount**. A negative difference indicates an underpayment; a positive difference indicates an overpayment. Missing and unexpected records have no calculated difference. For duplicate references, all summary amount fields are blank. A blank value means undetermined, not zero.

## Usage

1. Upload the expected and actual CSV files, or use the sample download buttons to obtain examples.
2. Click **Compare**.
3. Review the five status counts and the results table.
4. Use **Search payment reference**, **Status**, and **Show issues only** to narrow the table. All active filters must be satisfied.
5. Click **Download CSV report** to save `reconciliation_report.csv`.

Summary counts always describe all reference groups, not individual source rows. Filters only change the table and exported report. The download button is disabled when no results match. Clear the search, select **All statuses**, and uncheck **Show issues only** to export all results.

Changing either uploaded file clears the previous results and filters. Starting another comparison resets filters. Downloading a report preserves the current comparison.

## Sample results

Upload `samples/expected_payments.csv` and `samples/actual_payments.csv`. Their 16 source rows produce eight reference groups:

| Reference | Expected (TRY) | Actual (TRY) | Difference (TRY) | Status |
| --- | ---: | ---: | ---: | --- |
| PAY-001 | 1000.00 | 1000.00 | 0.00 | matched |
| PAY-002 | 2500.00 | 2300.00 | -200.00 | amount_mismatch |
| PAY-003 | 750.00 | | | missing |
| PAY-004 | | | | review_required |
| PAY-005 | 100.00 | 125.00 | 25.00 | amount_mismatch |
| PAY-006 | 1250.75 | 1250.75 | 0.00 | matched |
| PAY-007 | | | | review_required |
| PAY-099 | | 400.00 | | unexpected |

Expected counts: **2 matched, 2 amount mismatches, 1 missing, 1 unexpected, and 2 requiring review**.

## CSV report

The report uses these columns:

```csv
payment_reference,expected_amount,actual_amount,difference,status,description
PAY-002,2500.00,2300.00,-200.00,amount_mismatch,Actual payment is 200.00 TRY below the expected amount.
```

Amounts have two decimal places and no thousands separators. Missing values remain blank. The report uses UTF-8 with a BOM for character encoding recognition in Excel; commas, quotes, and line breaks are escaped using Python's CSV writer. When importing into a spreadsheet, select a comma delimiter and set the reference column to text to preserve leading zeros. Text fields are exported as supplied; the report does not neutralize spreadsheet formulas.

## Tests

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

The suite covers input validation and limits, duplicate handling, all five statuses, exact monetary differences, file replacement, combined filters, summary counts, and CSV report contents. Streamlit AppTest exercises interface interactions without requiring a running server. The current suite contains 74 tests. A `missing ScriptRunContext` warning may appear during AppTest runs; check the final test result (`OK`).

## Project files

| Path | Responsibility |
| --- | --- |
| `app.py` | Upload interface, comparison actions, summary, filters, and report download. |
| `reconciliation/models.py` | In-memory payment and result records. |
| `reconciliation/validation.py` | CSV parsing and input validation. |
| `reconciliation/engine.py` | Reference grouping, matching, and amount comparison. |
| `reconciliation/reporting.py` | CSV report generation. |
| `samples/` | Fictional input data and expected result fixture. |
| `tests/` | Business logic and UI interaction tests. |
| `.streamlit/config.toml` | Local server address, port, and telemetry setting. |

## Scope and limitations

This first version is intended for local, manual reconciliation. It supports TRY only and does not convert currencies, connect to banks, process payments, or match by dates or customer names. Split payments and repeated references require manual investigation.

There is no authentication, database, or saved comparison history. Uploaded data and results are held in application memory for the session; reports are saved only when downloaded. The server binds to `127.0.0.1` by default. No Docker setup or environment secrets are required.
