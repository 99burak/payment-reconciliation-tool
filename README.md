# Payment Reconciliation Tool

A small Python and Streamlit application that compares expected payments with actual payments from two CSV files.

## Status

Stages 1 (planning) and 2 (the first coding stage) are complete. The local Streamlit starter screen has been installed and verified. CSV upload, reconciliation, filtering, and export are planned for later stages.

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

The reconciliation modules and sample files will be created in their own stages.

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
git add app.py requirements.txt .gitignore .streamlit/config.toml README.md AGENTS.md docs
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

## Documents

- [Development instructions](AGENTS.md)
- [Project plan](docs/PROJECT_PLAN.md)
- [Architecture and data rules](docs/ARCHITECTURE.md)

These documents guide development; the application does not require them at runtime.
