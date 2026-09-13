import json
from pathlib import Path

from app.database import Database
from app.github_client import normalize_commit, normalize_contributor, normalize_issue, normalize_pull_request, normalize_repository


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "github_responses.json").read_text())


def records():
    repository = normalize_repository(FIXTURE["repository"])
    repository_id = repository["github_id"]
    return repository, [normalize_commit(FIXTURE["commit"], repository_id)], [normalize_contributor(FIXTURE["contributor"], repository_id)], [normalize_issue(FIXTURE["issue"], repository_id)], [normalize_pull_request(FIXTURE["pull_request"], repository_id)]


def test_initialize_creates_expected_tables(tmp_path):
    database = Database(tmp_path / "analytics.db")
    database.initialize()
    with database.connection() as connection:
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"repositories", "commits", "contributors", "issues", "pull_requests"} <= tables


def test_snapshot_replacement_is_idempotent_and_repository_scoped(tmp_path):
    database = Database(tmp_path / "analytics.db")
    snapshot = records()
    database.replace_repository_snapshot(*snapshot)
    database.replace_repository_snapshot(*snapshot)
    with database.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM repositories").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM commits").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM contributors").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM pull_requests").fetchone()[0] == 1