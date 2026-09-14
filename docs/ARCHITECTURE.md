# Architecture and Data Rules

## Technology

- Python for CSV parsing, validation, and reconciliation.
- Streamlit for a single-page interface.
- Python's standard library for CSV handling, exact decimal conversion, and core tests.
- In-memory processing during the session.

Stage 2 targets Python 3.12 and pins Streamlit 1.63.0. Installation and startup checks are recorded in the project plan. All files and application text use English.

## Database decision and data relationships

No persistent database is proposed for the first version. Users upload two files and download results; reopening historical runs is outside the initial scope. Therefore, there are no SQL tables, database relationships, or schema migrations to implement.

Data is still structured in memory:

| Data structure | Fields | Relationship |
|---|---|---|
| Expected payment | payment_reference, customer_name, amount_cents, source_row | Belongs to a result group through its reference. |
| Actual payment | transaction_id, payment_reference, amount_cents, source_row | Belongs to a result group through its reference. |
| Reconciliation result | payment_reference, status, difference_cents, description, expected_records, actual_records | Keeps the source records sharing the reference together. |

amount_cents stores the amount as an integer number of kuruş, the fractional unit of TRY. source_row identifies the input CSV row. These structures are not database tables.

A normal match has one expected record and one actual record. A duplicate-reference group can contain multiple source records and requires review.

## Authentication decision

Authentication checks who is using an application, for example through a username and password. Authorization determines what that identified user may do.

The initial tool is intended to run on the user's own computer, bound to localhost, for a single user. Localhost refers to the same computer. No user registration, login, password storage, roles, or login tokens are proposed for this scope.

Without authentication, anyone able to reach the application can use its interface. Local-only access is a scope and network-binding choice, not a login mechanism. Shared or public deployment would require a separate decision about access control, user isolation, and storage before publication.

Uploaded files will not be intentionally saved as persistent application files or database records. Users can save downloaded reports. In-memory processing is not a guarantee of secure memory erasure.

## Data flow

CSV upload → validation → normalized payment records → reference-based reconciliation → results → table and filters → CSV report.

Validation, reconciliation, and reporting will not depend on Streamlit. The interface calls these modules; it does not contain the business rules.

## Planned structure

```text
payment-reconciliation-tool/
  app.py
  requirements.txt
  .gitignore
  AGENTS.md
  reconciliation/
    __init__.py
    models.py
    validation.py
    engine.py
    reporting.py
  samples/
    expected_payments.csv
    actual_payments.csv
  tests/
    test_validation.py
    test_engine.py
    test_reporting.py
  docs/
    PROJECT_PLAN.md
    ARCHITECTURE.md
  README.md
```

app.py owns the interface and session state. models.py defines payment and result structures. validation.py parses and validates inputs. engine.py groups and reconciles records. reporting.py exports results. samples contains synthetic inputs, and tests checks behavior.

This is the target structure. Stage 2 adds app.py, requirements.txt, .gitignore, and .streamlit/config.toml. The reconciliation, samples, and tests directories will be introduced when their stages require them.

## CSV contract

Use UTF-8 encoding, optionally with a BOM, and a comma delimiter. Required column names must match the names below; their order may vary. Ignore entirely blank rows and extra columns. Reject duplicate column names and files without data rows.

### Expected payments

```csv
payment_reference,customer_name,amount
PAY-001,ABC Company,1000.00
PAY-002,XYZ Company,2500.00
```

All three fields are required. The customer name is for display, not matching.

### Actual payments

```csv
transaction_id,payment_reference,amount
TX-101,PAY-001,1000.00
TX-102,PAY-002,2300.00
```

All three fields are required. Transaction IDs must be unique within the actual file. Duplicate IDs are validation errors to prevent counting the same transaction twice.

### Normalization and validation

- Trim leading and trailing whitespace from fields.
- Preserve references as text, including leading zeros and letter case.
- Accept positive amounts with at most two decimal places: 1000, 1000.5, and 1000.50.
- Reject thousands separators, currency symbols, scientific notation, negative amounts, and zero.
- Parse amounts exactly and convert them to integer cents. Reject excess decimal places instead of rounding them.
- Treat all amounts as TRY and display this rule near the upload controls.
- Stop reconciliation when required fields, amounts, or CSV structure are invalid. Report the file and source row.
- Limit each upload to 5 MB and 10,000 data rows, with an explanatory error if exceeded.

## Reconciliation rules

Process the union of references from both files. Produce one result group per unique reference.

1. If either side contains multiple records for a reference, mark review_required. Preserve every source record without automatically summing or matching them.
2. If only the expected side contains the reference, mark missing.
3. If only the actual side contains the reference, mark unexpected.
4. If each side contains one record and amounts agree, mark matched.
5. If each side contains one record and amounts differ, mark amount_mismatch.

Calculate difference as actual minus expected. A negative difference means underpayment; a positive difference means overpayment. Leave difference empty for one-sided and duplicate groups. An absent record is not presented as a zero-valued payment.

## Results and interface

Each result group contains a reference, status, explanation, and source records. Unique pairs include expected amount, actual amount, and difference. Duplicate groups leave summary amount fields empty and expose source counts and details.

Display five status counters for the entire result set. Counters count reference groups rather than source rows. Show the number of visible groups separately after filtering.

Filters include status, reference search, and issues only. Issues include every status except matched.

Replacing or removing either uploaded file clears previous results, filters, and downloads. Reconcile only when the user presses the comparison button.

## CSV report

Export the currently filtered groups as reconciliation_report.csv. Use UTF-8 with BOM and two decimal places with a dot separator.

Columns: payment_reference, status, expected_amount, actual_amount, difference, expected_count, actual_count, description, expected_source_rows, actual_source_rows.

Source-row fields contain the relevant records as JSON text so duplicate groups remain inspectable. Quote CSV fields correctly. Protect user-supplied text from spreadsheet formula interpretation during export while keeping calculated numeric differences numeric.

## Verification plan

- All five result types and both signs of amount differences.
- Exact arithmetic for values such as 0.10.
- Preservation of source records when either or both inputs contain duplicate references.
- References with leading zeros and surrounding whitespace.
- Missing columns, malformed rows, empty files, invalid amounts, and duplicate transaction IDs.
- Export preserves records, commas, non-ASCII names, and formula-like input text.
- Replacing a file clears stale results, and filtered records agree with the downloaded report.
