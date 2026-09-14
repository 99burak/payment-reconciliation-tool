# Project Plan

## Goal

Replace manual comparison of two payment lists with a small tool that explains which payments match and which require investigation.

## Current state

The initial workspace contained a README and two planning documents. Stage 2 now adds the application starter screen, dependencies, local configuration, and Git ignore rules. Sample data and reconciliation code have not been implemented. A Git repository has not been initialized; the user will initialize it and make the first commit.

Git and uv are available. Stage 2 located bundled Python 3.12.14 and created a project-local .venv with Streamlit 1.63.0. Use .venv/Scripts/python.exe on this machine; the global python and py commands were not found on PATH.

All project files will be in English. Conversation explanations will remain in Turkish.

## Stages

- [x] 1. Inspect existing files and define scope, architecture, and workflow.
- [x] 2. Set up the Python and Streamlit project skeleton.
- [ ] 3. Create CSV templates and sample payment data.
- [ ] 4. Implement CSV parsing and validation.
- [ ] 5. Implement reference matching and amount comparison.
- [ ] 6. Handle duplicate references and unmatched payments.
- [ ] 7. Build the upload and reconciliation interface.
- [ ] 8. Add the results table, summary, and filters.
- [ ] 9. Add CSV report export.
- [ ] 10. Verify the complete workflow and finish the README.

Stage 1 was documentation only. The user authorized Stage 2 and confirmed that authentication is outside the initial version. Stage 2 is complete; Stage 3 requires a new user approval.

## Stage 2 verification results

- app.py syntax compilation: passed.
- Streamlit AppTest startup: passed without application exceptions.
- Local server request at 127.0.0.1:8501: HTTP 200.
- uv package compatibility check: all 37 installed packages compatible.
- Documentation link checks: passed.

The initial uv default-cache access issue was resolved by using a cache inside the workspace. Network permission was granted for package installation. No reconciliation features were added and no Git commit was made.

## Stage workflow

1. Inspect current files and Git status.
2. Explain the current stage's short plan.
3. Make only the authorized changes.
4. Run the relevant checks and resolve failures.
5. Explain important code, file responsibilities, and new concepts.
6. Report the result and suggest a commit message.
7. Wait for the user's commit and approval to proceed.

The user makes commits. Tests are added alongside the relevant implementation rather than postponed until the last stage. Documentation-only stages use consistency and link checks.

## Acceptance criteria

| Stage | Completion criteria |
|---|---|
| 1 | Scope, data contracts, reconciliation rules, and module responsibilities are documented. |
| 2 | A Python environment is verified, the Streamlit starter screen runs, and requirements and .gitignore exist. Explain local Git setup to the user. |
| 3 | Synthetic input files cover all five result types, with manually verified expected results. |
| 4 | Valid CSV files load; missing columns, empty required fields, and invalid amounts produce file and source-row errors. |
| 5 | Unique references produce correct matches and signed amount differences. |
| 6 | Duplicate groups preserve their records for review; missing and unexpected payments are identified correctly. |
| 7 | Two uploads can be compared with a button; replacing an input clears stale results. |
| 8 | The table, five status counters, status filter, and reference search work. |
| 9 | Downloaded CSV contains the same groups as the filtered view. |
| 10 | Relevant tests pass, the complete user flow is checked, and the README explains setup and use. |

## Estimated schedule

| Day | Work |
|---|---|
| 1 | Stages 1–5: plan, setup, data, and core reconciliation |
| 2 | Stages 6–9: edge cases, interface, and export |
| 3 | Stage 10: complete workflow checks and documentation |
| 4 | Remaining fixes and presentation polish, if needed |

The schedule is an estimate. Correct behavior is the completion requirement.

## Scope boundaries

The first version uses TRY and expects at most one payment on each side per reference. Duplicate references require review. Partial-payment aggregation, refunds, exchange rates, bank connections, user accounts, and report history are deferred.

## Demo acceptance scenario

| Reference | Expected | Actual | Result |
|---|---:|---:|---|
| PAY-001 | 1000.00 | 1000.00 | Matched |
| PAY-002 | 2500.00 | 2300.00 | Amount mismatch; difference -200.00 |
| PAY-003 | 750.00 | — | Missing payment |
| PAY-099 | — | 400.00 | Unexpected payment |
| PAY-004 | 500.00 | Two separate 500.00 records | Review required: duplicate reference |

Summary counters count reference groups, not source rows. This example contains one group per status. PAY-004 is not automatically summed or matched; both actual records remain inspectable.

## Suggested commit messages

| Stage | Message |
|---|---|
| 1 | docs: define project scope and staged development workflow |
| 2 | chore: initialize Python and Streamlit project |
| 3 | test: add sample payment files and expected results |
| 4 | feat: validate payment CSV files |
| 5 | feat: reconcile payments by reference and amount |
| 6 | feat: handle duplicate and unmatched payments |
| 7 | feat: add payment file upload interface |
| 8 | feat: display reconciliation summary and filters |
| 9 | feat: export reconciliation results to CSV |
| 10 | test: verify application flow and document usage |

Adjust messages to the actual completed changes. The user can initialize the repository in the project folder with git init before the first commit. This creates local version history; it does not publish anything to GitHub.
