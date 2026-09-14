# Development Instructions

This project is being developed with the user one stage at a time, with an emphasis on learning.

1. Inspect existing files and Git status before changing anything.
2. Explain a short plan for the current stage before writing code.
3. Implement only the stage authorized by the user. Wait for approval before starting the next stage.
4. Run relevant tests or the application after every implementation stage. Resolve errors before proceeding. If a check cannot run, explain why and do not report it as passed.
5. For documentation-only changes, verify consistency and local links. Inspect the Git diff when a repository exists. Do not claim application tests ran when no application exists.
6. Explain important code, file responsibilities, and unfamiliar concepts in plain Turkish.
7. Keep every project file in English, including filenames, documentation, identifiers, comments, tests, interface text, and error messages.
8. Avoid unnecessary abstraction and overengineering. The target is a small payment reconciliation tool achievable in approximately 2–4 working days.
9. At the end of each stage, report changes, checks, their results, and a suggested English Git commit message.
10. The user makes commits. Do not run git add, git commit, or git push unless explicitly requested.
11. Before a new stage, report any uncommitted changes from the previous stage. Do not delete, revert, or mix them with the next stage without the user's approval.
12. Reconsider database and authentication decisions if the scope changes. A request to explain a feature does not authorize implementing it.

## Proposed initial architecture

Python and Streamlit, two CSV inputs, TRY amounts, reference-based reconciliation, filtering, and CSV export. Data is processed in memory. A persistent database and user accounts are outside the initial scope.

See docs/PROJECT_PLAN.md and docs/ARCHITECTURE.md for details.
