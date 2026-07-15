# Hermes Agent OS Improvement Proposals

## Overview
Based on the current state of the Hermes Agent OS repository (16 TypeScript packages, 7 Python modules, existing CI for TypeScript only, limited documentation, no versioning/issue tracking), the following improvements are recommended to improve code quality, reliability, and developer experience.

---

## Proposal 1: Add Python Testing and Coverage to CI
**Problem:** No automated tests for Python modules; no code coverage gate.
**Impact:** High – prevents regressions in core Python components (DNA engine, research, agency, etc.).
**Cost:** Low – mostly configuration and adding test files.
**Priority:** P0

### Steps:
1. Add `pytest` and `pytest-cov` to `packages/*/pyproject.toml` or `requirements-dev.txt`.
2. Create a basic test suite for each Python package (e.g., `packages/dna_engine/test_model_health.py`).
3. Update `.github/workflows/ci.yaml`:
   - Add a step to install Python dependencies (using `pip install -r packages/*/requirements.txt` or use `uv`).
   - Run `pytest --cov=packages --cov-report=term-missing` under the `test` job.
   - Add a coverage gate (e.g., `--cov-fail-under=80`).
4. Add a `test` script to the root `package.json` (via `turbo`) to run Python tests alongside JS tests.
5. Optionally, add `ruff format` check in CI.

### Expected Outcome:
- Python code is tested on every push/PR.
- Coverage threshold ensures new code is tested.
- Early detection of regressions in core logic.

---

## Proposal 2: Implement Automated Versioning and Changelog Generation
**Problem:** No centralized versioning; changelog is fragmented (multiple CHANGELOG_PHASE*.md files). Hard to track releases.
**Impact:** Medium – improves release management and visibility for users/maintainers.
**Cost:** Low – adopt an established tool.
**Priority:** P1

### Steps:
1. Choose a tool: `changesets` (works well with monorepos) or `semantic-release` with conventional commits.
2. Initialize the tool:
   - For changesets: `npx changeset init` → adds `.changeset` config.
   - Add a `changeset` script to `package.json`.
3. Configure the workflow to:
   - On PR, prompt for a changeset (via GitHub Action from `changesets/action`).
   - On merge to `master`, run `changeset version` and `changeset publish` to update `package.json` versions and generate a consolidated `CHANGELOG.md`.
4. Remove the fragmented `CHANGELOG_PHASE*.md` files and maintain a single `CHANGELOG.md`.
5. Add a `RELEASE.md` guide for maintainers.

### Expected Outcome:
- Automated version bumps based on conventional commits.
- Clear, searchable changelog for users.
- Reduced manual release overhead.

---

## Proposal 3: Consolidate and Expand Documentation
**Problem:** Documentation is sparse (only `CODE_REVIEW.md` and `AGENTS.md`). Users and contributors lack guidance.
**Impact:** Medium – improves onboarding and reduces support overhead.
**Cost:** Medium – requires writing but can leverage existing knowledge.
**Priority:** P1

### Steps:
1. Create a structured `docs/` directory (if not already) with subfolders:
   - `docs/user-guide/` – end‑user guide for Hermes Desktop.
   - `docs/developer/` – contributing guide, setup, coding standards.
   - `docs/api/` – API references.
2. Generate API docs:
   - For TypeScript: add `typedoc` to dev dependencies, add a script to generate HTML/JSON, commit to `docs/api/ts`.
   - For Python: use `sphinx` with `autodoc` to generate docs from docstrings, output to `docs/api/python`.
3. Write a getting‑started guide, architecture overview (based on existing README), and troubleshooting FAQ.
4. Add a documentation lint step (e.g., `markdownlint`) to CI.
5. Link the docs from the repository README.

### Expected Outcome:
- Centralized, up‑to‑date documentation.
- Easier onboarding for new contributors and users.
- Professional appearance for the project.

---

## Proposal 4: Standardize Issue and Bug Tracking
**Problem:** No issue templates, no contribution guidelines, ad‑hoc bug reporting.
**Impact:** Medium – improves triage and contributor experience.
**Cost:** Low – mainly adding templates and a CONTRIBUTING file.
**Priority:** P2

### Steps:
1. Create `.github/ISSUE_TEMPLATE/` with:
   - `bug_report.yml`
   - `feature_request.yml`
   - `question.yml`
2. Add a `.github/CONTRIBUTING.md` that outlines:
   - How to report a bug.
   - How to propose a feature.
   - Coding style (reference existing linters/formatter).
   - Pull request process.
3. Enable GitHub Projects (or use a simple Kanban) to track sprints.
4. Optionally, add a `CONTRIBUTING` section to the README linking to the above.

### Expected Outcome:
- Consistent issue reports.
- Clear path for external contributions.
- Reduced duplicate issues.

---

## Proposal 5: Add Pre‑Commit Hooks for Code Quality
**Problem:** Linting and formatting are only checked in CI; developers may push code that fails CI.
**Impact:** Low‑Medium – catches issues early, reduces CI failures.
**Cost:** Low – using `pre-commit` framework.
**Priority:** P2

### Steps:
1. Add `pre-commit` config (`.pre-commit-config.yaml`) with hooks:
   - `ruff` (Python lint/format)
   - `prettier` (TypeScript/JSON/Markdown)
   - `trivy` or `detect-secrets` for secret scanning (optional)
2. Add a `prepare` script in root `package.json` that runs `npx husky install` (or use `pre-commit` directly).
3. Document the setup in `CONTRIBUTING.md`.
4. (Optional) Add a CI step that runs `pre-commit run --all-files` to ensure compliance.

### Expected Outcome:
- Code formatted and linted before commit.
- Fewer CI failures due to style issues.
- Consistent codebase.

---

## Summary of Priorities
| Priority | Proposal | Cost | Impact |
|----------|----------|------|--------|
| P0 | Add Python testing & coverage to CI | Low | High |
| P1 | Automated versioning & changelog | Low | Medium |
| P1 | Consolidate & expand documentation | Medium | Medium |
| P2 | Standardize issue/bug tracking | Low | Medium |
| P2 | Pre‑commit hooks for code quality | Low | Low‑Medium |

Implementing the top two (Python testing/CD and automated versioning) will give the biggest immediate boost in reliability and release management. Documentation and issue tracking improve long‑term maintainability, while pre‑commit polishes the developer experience.

--- 
*Generated by Hermes CTO Agent on 2026-07-15.*