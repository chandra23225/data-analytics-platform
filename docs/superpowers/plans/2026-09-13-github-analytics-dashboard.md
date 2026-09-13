# GitHub Analytics Dashboard MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit dashboard that ingests public GitHub repository data into SQLite and presents repository, activity, contributor, and comparison analytics.

**Architecture:** Keep the application split into pure data contracts, GitHub transport, SQLite persistence, SQL analytics, and Streamlit presentation. The dashboard calls an ingestion service, while analytics can run against fixture data without network access.

**Tech Stack:** Python 3.11+, Streamlit, requests, pandas, SQLite, pytest, python-dotenv.

---

## File Map

- Create `app/__init__.py`: package marker.
- Create `app/github_client.py`: URL parsing and GitHub API transport.
- Create `app/database.py`: SQLite initialization and repository-scoped upserts.
- Create `app/analytics.py`: parameterized dashboard queries.
- Create `app/dashboard.py`: Streamlit controls and visualizations.
- Create `sql/schema.sql`: relational schema.
- Create `requirements.txt`: runtime and test dependencies.
- Create `.env.example`: optional GitHub token configuration.
- Create `.gitignore`: Python, SQLite, and local environment exclusions.
- Create `tests/fixtures/github_responses.json`: deterministic API fixture data.
- Create `tests/test_github_client.py`: URL parsing and normalization tests.
- Create `tests/test_database.py`: schema and upsert tests.
- Create `tests/test_analytics.py`: SQL metric tests.
- Replace `README.md`: setup, usage, data model, and test instructions.

### Task 1: Bootstrap the Python project

**Files:** `requirements.txt`, `.env.example`, `.gitignore`, `app/__init__.py`, `tests/__init__.py`

- [ ] Write the project files with Python 3.11-compatible dependencies: `streamlit`, `requests`, `pandas`, `python-dotenv`, and `pytest`.
- [ ] Add `GITHUB_TOKEN=`, `DATABASE_PATH=data/github_analytics.db`, and `GITHUB_API_URL=https://api.github.com` to `.env.example`.
- [ ] Ignore `.venv/`, `__pycache__/`, `.pytest_cache/`, `.env`, `data/*.db`, and Streamlit cache files.
- [ ] Run `python -m pytest -q` and verify collection succeeds with zero tests.
- [ ] Commit with `chore: bootstrap analytics platform`.

### Task 2: Add GitHub URL parsing and API normalization

**Files:** `app/github_client.py`, `tests/test_github_client.py`, `tests/fixtures/github_responses.json`

- [ ] Write failing tests for `parse_repository_url("https://github.com/psf/requests") == ("psf", "requests")`, trailing slashes, `.git` suffixes, and malformed/non-GitHub URLs raising `ValueError`.
- [ ] Write fixture-backed tests for `normalize_repository`, `normalize_commit`, `normalize_contributor`, `normalize_issue`, and `normalize_pull_request`; each returns stable fields including the GitHub numeric ID and repository full name.
- [ ] Run `python -m pytest tests/test_github_client.py -q` and verify the new tests fail because the module is missing.
- [ ] Implement `GitHubClient` with a `requests.Session`, optional bearer token, `Accept: application/vnd.github+json`, timeout, and methods for repository metadata, commits, contributors, issues, and pull requests.
- [ ] Raise typed `GitHubApiError` values containing status code and endpoint for HTTP failures while preserving the response body only as a short message.
- [ ] Run `python -m pytest tests/test_github_client.py -q` and verify all client tests pass.
- [ ] Commit with `feat: add GitHub ingestion client`.

### Task 3: Add SQLite schema and persistence

**Files:** `sql/schema.sql`, `app/database.py`, `tests/test_database.py`

- [ ] Write tests using `tmp_path` that initialize a database, confirm tables `repositories`, `commits`, `contributors`, `issues`, and `pull_requests` exist, and verify repository-scoped upserts do not duplicate records.
- [ ] Run `python -m pytest tests/test_database.py -q` and verify failure because persistence functions are missing.
- [ ] Define tables with stable GitHub IDs, repository foreign keys, ISO timestamps, indexes on repository and event date, and `ON CONFLICT` upsert behavior.
- [ ] Implement `Database.initialize()`, `upsert_repository()`, `replace_repository_snapshot()`, and `connection()` using `sqlite3` and transaction context managers.
- [ ] Ensure snapshot replacement deletes only child records for the targeted repository before inserting the fresh normalized records, preserving other repositories and cached data on failed ingestion.
- [ ] Run `python -m pytest tests/test_database.py -q` and verify all database tests pass.
- [ ] Commit with `feat: add SQLite persistence layer`.

### Task 4: Add SQL analytics

**Files:** `sql/analytics.sql`, `app/analytics.py`, `tests/test_analytics.py`

- [ ] Seed an in-memory or temporary SQLite database from fixture records and write tests for overview totals, daily activity counts, contributor ranking, and multi-repository comparison.
- [ ] Run `python -m pytest tests/test_analytics.py -q` and verify the tests fail before query functions exist.
- [ ] Add parameterized SQL queries that filter by repository IDs and inclusive UTC date bounds; never interpolate user input into SQL.
- [ ] Implement `get_overview()`, `get_activity_trend()`, `get_contributor_ranking()`, and `get_repository_comparison()` returning pandas DataFrames with stable column names.
- [ ] Run `python -m pytest tests/test_analytics.py -q` and verify all analytics tests pass.
- [ ] Commit with `feat: add SQL analytics queries`.

### Task 5: Build the Streamlit dashboard

**Files:** `app/dashboard.py`, `README.md`

- [ ] Add a sidebar for repository URL entry, a refresh action, repository selection, and date-range controls.
- [ ] On refresh, parse each URL, fetch all supported GitHub resources, and call `replace_repository_snapshot()` only after the complete repository snapshot is available.
- [ ] Display cached data when refresh fails, with repository-specific error messages and a visible last-fetched timestamp.
- [ ] Render overview metrics, activity line charts, contributor tables, and a comparison table using the analytics module; show explicit empty states when no data is selected.
- [ ] Keep the dashboard import-safe by placing Streamlit execution behind `main()` and `if __name__ == "__main__":`.
- [ ] Update README with setup commands, `streamlit run app/dashboard.py`, optional token setup, supported metrics, and fixture/test commands.
- [ ] Run `python -m streamlit run app/dashboard.py --server.headless true` and verify the process starts without import errors, then stop it.
- [ ] Commit with `feat: add interactive GitHub analytics dashboard`.

### Task 6: Verify the MVP end to end

**Files:** existing project files only

- [ ] Run `python -m pytest -q` and verify the complete test suite passes.
- [ ] Run `python -m compileall app tests` and verify there are no syntax errors.
- [ ] Launch Streamlit with a temporary fixture database and verify the dashboard serves its root page successfully.
- [ ] Run `git diff --check` and verify there are no whitespace errors.
- [ ] Review the README against the design document and commit with `test: verify analytics dashboard MVP`.