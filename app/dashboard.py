"""Streamlit dashboard for GitHub repository analytics."""

from __future__ import annotations

import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from app.analytics import get_activity_trend, get_contributor_ranking, get_overview, get_repository_comparison
from app.database import Database
from app.github_client import GitHubApiError, GitHubClient, normalize_commit, normalize_contributor, normalize_issue, normalize_pull_request, normalize_repository, parse_repository_url


def ingest_repository(database: Database, client: GitHubClient, url: str) -> str:
    owner, repository_name = parse_repository_url(url)
    repository = normalize_repository(client.repository(owner, repository_name))
    repository_id = repository["github_id"]
    commits = [normalize_commit(item, repository_id) for item in client.commits(owner, repository_name)]
    contributors = [normalize_contributor(item, repository_id) for item in client.contributors(owner, repository_name)]
    issues = [normalize_issue(item, repository_id) for item in client.issues(owner, repository_name) if not item.get("pull_request")]
    pull_requests = [normalize_pull_request(item, repository_id) for item in client.pull_requests(owner, repository_name)]
    database.replace_repository_snapshot(repository, commits, contributors, issues, pull_requests)
    return repository["full_name"]


def main() -> None:
    load_dotenv()
    database = Database(os.getenv("DATABASE_PATH", "data/github_analytics.db"))
    database.initialize()
    client = GitHubClient(token=os.getenv("GITHUB_TOKEN") or None, base_url=os.getenv("GITHUB_API_URL", "https://api.github.com"))

    st.set_page_config(page_title="GitHub Analytics", page_icon="GH", layout="wide")
    st.title("GitHub Analytics")
    st.caption("Local-first repository intelligence backed by SQLite")

    with st.sidebar:
        st.header("Repositories")
        urls = st.text_area("Repository URLs", placeholder="https://github.com/owner/repository\nhttps://github.com/another/project")
        refresh = st.button("Refresh data", type="primary", use_container_width=True)
        if refresh:
            for raw_url in [line.strip() for line in urls.splitlines() if line.strip()]:
                try:
                    name = ingest_repository(database, client, raw_url)
                    st.success(f"Updated {name}")
                except (ValueError, GitHubApiError) as error:
                    st.error(str(error))

    with database.connection() as connection:
        repositories = connection.execute("SELECT github_id, full_name, fetched_at FROM repositories ORDER BY full_name").fetchall()
        if not repositories:
            st.info("Add a public GitHub repository URL in the sidebar to begin.")
            return
        repository_options = {row["full_name"]: row["github_id"] for row in repositories}
        selected_names = st.multiselect("Repositories", list(repository_options), default=list(repository_options))
        selected_ids = [repository_options[name] for name in selected_names]
        if not selected_ids:
            st.warning("Select at least one repository to view analytics.")
            return

        default_start = date.today() - timedelta(days=90)
        start_date, end_date = st.date_input("Activity date range", value=(default_start, date.today()))
        overview = get_overview(connection, selected_ids).iloc[0]
        metrics = st.columns(7)
        for column, label, value in zip(metrics, ["Repositories", "Stars", "Forks", "Open issues", "Commits", "Contributors", "Pull requests"], [overview.repository_count, overview.stars, overview.forks, overview.open_issues, overview.commits, overview.contributors, overview.pull_requests]):
            column.metric(label, int(value))

        st.subheader("Activity")
        trend = get_activity_trend(connection, selected_ids, start_date.isoformat(), end_date.isoformat())
        st.line_chart(trend.set_index("activity_date") if not trend.empty else trend)

        left, right = st.columns(2)
        with left:
            st.subheader("Top contributors")
            st.dataframe(get_contributor_ranking(connection, selected_ids), use_container_width=True, hide_index=True)
        with right:
            st.subheader("Repository comparison")
            st.dataframe(get_repository_comparison(connection, selected_ids), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()