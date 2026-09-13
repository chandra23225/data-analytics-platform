# GitHub Analytics Platform

Local-first Python and SQL analytics for public GitHub repositories.

## Quick start

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app/dashboard.py
```

Open the local Streamlit URL, enter one or more public GitHub repository URLs, and choose **Refresh data**. A GitHub token is optional, but setting `GITHUB_TOKEN` in `.env` raises the API rate limit.

## Dashboard metrics

- Repository overview: repositories, stars, forks, open issues, commits, contributors, and pull requests.
- Activity trends: daily commits, issues, and pull requests for a selectable date range.
- Contributor ranking across the selected repositories.
- Repository comparison by popularity and activity.

Data is cached in `data/github_analytics.db`. A failed refresh leaves the previous snapshot available.

## Development

Run the test suite and syntax check with:

```powershell
python -m pytest -q
python -m compileall app tests
```

The tests use local fixtures and do not require GitHub network access. SQL schema and analytics queries live in `sql/`.
