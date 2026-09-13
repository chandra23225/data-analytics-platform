# GitHub Analytics Dashboard MVP

## Goal

Build a local-first Python and SQL analytics platform that lets a user inspect public GitHub repository activity through an interactive dashboard.

## Scope

The first release supports repository URLs, GitHub REST API ingestion, SQLite persistence, SQL-backed analytics, and a Streamlit dashboard. It covers repository overview metrics, activity trends, contributor analysis, and comparison across configured repositories.

Cloud deployment, scheduled ingestion, user accounts, PostgreSQL, and private repository workflows are explicitly deferred.

## Architecture

- `app/github_client.py` fetches repository metadata, commits, contributors, issues, and pull requests from GitHub.
- `app/database.py` initializes SQLite, applies the schema, and stores normalized records.
- `app/analytics.py` executes parameterized SQL queries and returns dashboard-ready data.
- `app/dashboard.py` provides the Streamlit user interface, filters, charts, and refresh actions.
- `sql/schema.sql` defines the relational tables.
- `sql/analytics.sql` contains reusable analytics queries and views.

The GitHub token is optional and is read from an environment variable. Public repositories work without credentials, subject to GitHub API limits.

## Data Flow

1. The user submits one or more GitHub repository URLs.
2. The application validates and normalizes each URL.
3. The client fetches available GitHub data and reports API or repository errors clearly.
4. Normalized records are upserted into SQLite with repository and retrieval timestamps.
5. SQL queries calculate metrics for the selected repositories and date range.
6. Streamlit renders metric cards, charts, tables, and comparison results.

## Data Model

The initial schema contains repositories, commits, contributors, issues, and pull requests. Records use GitHub identifiers as stable natural keys where available, with foreign keys back to repositories. Retrieval timestamps support cache visibility and future refresh policies.

## User Experience

The dashboard opens with repository input and a refresh action. After data is available, users can select repositories and a date range. The main view shows overview metrics, activity trends, contributor rankings, and a comparison table. Empty states explain when a repository has not been ingested; API failures identify the affected repository without hiding successful results from others.

## Error Handling

- Reject malformed repository URLs before making network requests.
- Surface not-found, rate-limit, authentication, and transient API errors in the dashboard.
- Preserve previously cached data when a refresh fails.
- Allow analytics to run against fixture data for offline development and tests.

## Testing

- Unit tests cover URL parsing, API response normalization, database upserts, and analytics query behavior.
- Fixture-based tests avoid requiring GitHub network access.
- A smoke check launches Streamlit and verifies the application starts successfully.

## Deferred Extensions

The schema and module boundaries should allow later addition of PostgreSQL, scheduled ingestion, private repository authentication, deployment configuration, and more advanced insights without changing the dashboard's core contracts.