# Payment Reconciliation Tool

A lightweight tool for reconciling expected and actual payments from CSV files. Built with Python and Streamlit.

## Status

Stages 1–4 (planning, the project skeleton, sample payment data, and CSV loading and validation) are complete. Stage 5 is in progress: reference pairing is implemented, while amount comparison is pending. The Streamlit screen is still the starter screen; upload controls, complete reconciliation, filtering, and export are planned for later stages.

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
| reconciliation/models.py | Defines expected and actual payment records held in memory. |
| reconciliation/validation.py | Reads CSV bytes, checks inputs, and converts amounts into integer cents. |
| reconciliation/__init__.py | Identifies the reconciliation directory as a Python package. |
| tests/test_validation.py | Exercises valid files, invalid data, exact amounts, and input limits. |
| reconciliation/engine.py | Pairs records whose reference appears exactly once in each input. |
| tests/test_engine.py | Checks reference pairing, ambiguous references, and preservation of inputs. |

Amount comparison, complete reconciliation, and reporting will be added in their own steps.

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

## CSV loading and validation

The loaders use Python's standard library and do not depend on Streamlit. Pass the file contents as bytes and, optionally, a filename for error messages:

```python
from pathlib import Path

from reconciliation.validation import load_actual_payments, load_expected_payments

expected_file = Path("samples/expected_payments.csv")
actual_file = Path("samples/actual_payments.csv")

expected = load_expected_payments(expected_file.read_bytes(), expected_file.name)
actual = load_actual_payments(actual_file.read_bytes(), actual_file.name)

print(len(expected), len(actual))  # 8 8
print(expected[5].amount_cents)  # 125075 represents 1250.75 TRY
```

Each loader returns the complete list of validated records or raises CSVValidationError. It never returns a partially accepted file. source_row records the starting physical line of a payment, including when earlier quoted fields span multiple lines.

Validation rules:

- Accept UTF-8, including UTF-8 BOM, with comma-separated fields.
- Trim surrounding whitespace; preserve reference case and leading zeros.
- Accept required columns in any order and ignore additional named columns.
- Reject missing, duplicate, or empty column names and missing required values.
- Ignore fully blank rows; reject empty files and files with no payments.
- Accept positive amounts such as 10, 10.5, and 10.50. Reject zero, negatives, comma decimal separators, thousands separators, currency symbols, and more than two decimal places.
- Convert amounts directly to integer cents without floating-point arithmetic or rounding.
- Reject repeated transaction IDs after trimming. Repeated payment references are preserved for the future reconciliation stage.
- Reject malformed CSV, mismatched field counts, and invalid UTF-8.
- Accept up to 5 MiB (5,242,880 bytes) and 10,000 nonblank payment rows per file.

Errors identify the filename and source line when applicable. For example:

```text
payments.csv, row 3: Required field 'amount' is empty.
```

models.py uses dataclasses: simple Python record definitions with named fields. ExpectedPayment contains a reference, customer name, amount_cents, and source_row. ActualPayment contains a transaction ID, reference, amount_cents, and source_row. These are in-memory records, not database tables.

## Reference pairing (Stage 5, step 1)

match_unique_payments in reconciliation/engine.py accepts the two validated payment lists and returns PaymentPair records. Each pair keeps the original expected and actual records together, including their amounts and source lines. Pairs follow the expected input order; the actual file can be ordered differently.

```python
from reconciliation.engine import match_unique_payments

# expected and actual are the lists loaded in the example above.
pairs = match_unique_payments(expected, actual)
for pair in pairs:
    print(pair.expected.payment_reference, pair.actual.transaction_id)
```

The sample files produce four pairs: PAY-001, PAY-002, PAY-005, and PAY-006. Pairing only connects references; it does not assign matched/amount_mismatch statuses or calculate differences yet.

A reference must occur exactly once on each side to form a pair. Duplicate or one-sided references are excluded from this partial result, with all input records left unchanged. Their classification is a later stage. The returned pairs are not a complete reconciliation report.

Step 1 verification: all 8 reference-pairing tests passed, together with the existing 24 validation tests (32 total). No user interface changes were made in this step.

## Tests

Run the tests from the project folder with Python's built-in unittest runner; no additional test package is required:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Stage 4 verification: all 24 validation tests passed, including both sample input files, exact fractional amounts, input errors, preserved duplicate references, and size/row limit boundaries. Reconciliation results are not calculated in this stage.

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
