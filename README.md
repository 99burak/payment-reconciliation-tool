# Payment Reconciliation Tool

A lightweight tool for reconciling expected and actual payments from CSV files. Built with Python and Streamlit.

## Status

Stages 1 (planning), 2 (the project skeleton), and 3 (sample payment data) are complete. The local Streamlit starter screen and sample CSV files are available. CSV parsing, upload, reconciliation, filtering, and export are planned for later stages.

## Setup

Use Python 3.12 and run commands from the project folder. Create a virtual environment, which keeps this project's installed packages separate from other projects:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you use uv, a Python environment and package manager, the equivalent commands are:

```powershell
uv --cache-dir .uv-cache venv --python 3.12 .venv
uv --cache-dir .uv-cache pip install --python .venv\Scripts\python.exe -r requirements.txt
```

The local environment created during development is already installed in .venv. If it exists and dependencies have been installed, go directly to Run. Virtual environments are local and are not committed to Git.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://127.0.0.1:8501 in your browser. Stop the server with Ctrl+C in the terminal. The configuration binds the server to this computer only; no login is required for the initial version.

## Current files

| File | Responsibility |
|---|---|
| app.py | Displays the starter screen and planned user workflow. |
| requirements.txt | Pins the direct application dependency, Streamlit. |
| .streamlit/config.toml | Configures local-only access, port 8501, and disables usage statistics. |
| .gitignore | Keeps environments, caches, secrets, and local data out of commits. |
| samples/expected_payments.csv | Synthetic expected payments; also serves as the expected-payment CSV template. |
| samples/actual_payments.csv | Synthetic actual payments; also serves as the actual-payment CSV template. |
| samples/expected_results.csv | Manually specified expected outcomes for verifying the future reconciliation engine. |

The reconciliation modules will be created in their own stages.

## Sample payment data

The sample files contain fictional data. Keep the header row when replacing sample rows with your own data. Save inputs as UTF-8 CSV with a comma separator. Amounts are positive TRY values with a dot decimal separator, at most two decimal places, and no thousands separator or currency symbol.

- Expected payments require payment_reference, customer_name, and amount.
- Actual payments require transaction_id, payment_reference, and amount. Transaction IDs are unique within the file.
- payment_reference is the shared identifier used to connect an expected payment to an actual payment. Customer names are display information, not matching keys.
- The two input files each contain 8 payment rows. Together they contain 8 distinct references.

expected_results.csv is a reference file, not a third payment input or an application-generated report. Its amounts use TRY. expected_count and actual_count indicate how many source rows share the reference.

| Reference | Expected outcome | Explanation |
|---|---|---|
| PAY-001 | matched | Both amounts are 1000.00. |
| PAY-002 | amount_mismatch | Expected 2500.00; received 2300.00; difference -200.00. |
| PAY-003 | missing | Expected 750.00; no actual record exists. |
| PAY-004 | review_required | One expected record and two actual records share the reference. |
| PAY-005 | amount_mismatch | Expected 100.00; received 125.00; difference +25.00. |
| PAY-006 | matched | Both amounts are 1250.75, including fractional currency units. |
| PAY-007 | review_required | Two expected records and one actual record share the reference. |
| PAY-099 | unexpected | Received 400.00; no expected record exists. |

For unique pairs, difference means actual amount minus expected amount. A negative difference indicates underpayment; a positive difference indicates overpayment. An absent payment and a difference that cannot be calculated are left blank rather than represented as zero.

Duplicate references require review even if adding their amounts would produce a match. They are not automatically summed or paired. Both summary amount fields and the difference are left blank for these groups; source-row counts identify the ambiguity.

The expected summary counts reference groups: 2 matched, 2 amount mismatches, 1 missing, 1 unexpected, and 2 requiring review.

Sample-data verification passed: all three CSV schemas and row counts, required input fields, positive two-decimal amounts, unique transaction IDs, source reference counts, and all eight manually specified outcomes were checked. Amount differences were verified using exact decimal arithmetic. These checks validate the examples; they do not represent tests of an implemented reconciliation engine.

## Stage 2 verification

Verified with Python 3.12.14 and Streamlit 1.63.0:

- Python syntax compilation passed.
- Streamlit AppTest executed the starter screen without application exceptions.
- The local server returned HTTP 200 at http://127.0.0.1:8501.
- Package compatibility checks passed.
- Local documentation links resolved correctly.

This is a startup check, not a test of reconciliation features, which have not been implemented yet. The temporary verification script is a development artifact outside the repository. A repeatable starter-screen check from the project folder is:

```powershell
.\.venv\Scripts\python.exe -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('app.py').run(); assert not app.exception; print('Startup check passed')"
```

## First commit

No commit has been made by the assistant. If this folder is not a Git repository yet, run git init here, then review and commit the project files:

```powershell
git init
git add app.py requirements.txt .gitignore .streamlit/config.toml README.md
git diff --cached --stat
git commit -m "chore: initialize Python and Streamlit project"
```

The local .venv directory is ignored. These commands create local history and do not publish the project to GitHub.

## Initial scope

- Upload two CSV files with predefined columns.
- Validate required fields and payment amounts.
- Match payments by reference and compare amounts in integer cents.
- Identify matched, mismatched, missing, unexpected, and duplicate-reference groups.
- Filter results and download a CSV report.
- Process data in memory for local, single-user use.

The target is a functional first version in approximately 2–4 working days. Partial payments, refunds, currency conversion, bank integrations, user accounts, and report history are outside this version.

## Language

All project filenames, documentation, source code identifiers, comments, tests, user interface text, and error messages will use English. Explanations in the conversation will remain in Turkish.
