import json
from pathlib import Path

from app.analytics import get_activity_trend, get_contributor_ranking, get_overview, get_repository_comparison
from app.database import Database
from app.github_client import normalize_commit, normalize_contributor, normalize_issue, normalize_pull_request, normalize_repository


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "github_responses.json").read_text())


def seeded_database(tmp_path):
    database = Database(tmp_path / "analytics.db")
    repository = normalize_repository(FIXTURE["repository"])
    repository_id = repository["github_id"]
    database.replace_repository_snapshot(
        repository,
        [normalize_commit(FIXTURE["commit"], repository_id)],
        [normalize_contributor(FIXTURE["contributor"], repository_id)],
        [normalize_issue(FIXTURE["issue"], repository_id)],
        [normalize_pull_request(FIXTURE["pull_request"], repository_id)],
    )
    return database, repository_id


def test_analytics_returns_overview_and_rankings(tmp_path):
    database, repository_id = seeded_database(tmp_path)
    with database.connection() as connection:
        overview = get_overview(connection, [repository_id]).iloc[0]
        ranking = get_contributor_ranking(connection, [repository_id])
        comparison = get_repository_comparison(connection, [repository_id])
    assert overview["stars"] == 10
    assert overview["commits"] == 1
    assert ranking.iloc[0].to_dict() == {"login": "alice", "contributions": 4}
    assert comparison.iloc[0]["full_name"] == "psf/requests"


def test_activity_trend_filters_date_range(tmp_path):
    database, repository_id = seeded_database(tmp_path)
    with database.connection() as connection:
        trend = get_activity_trend(connection, [repository_id], "2024-01-01", "2024-01-05")
    assert set(trend["activity_date"]) == {"2024-01-03", "2024-01-04", "2024-01-05"}
    assert trend.loc[trend["activity_date"] == "2024-01-03", "commits"].iloc[0] == 1