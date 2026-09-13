import json
from pathlib import Path

import pytest

from app.github_client import (
    normalize_commit,
    normalize_contributor,
    normalize_issue,
    normalize_pull_request,
    normalize_repository,
    parse_repository_url,
)


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "github_responses.json").read_text()
)


def test_parse_repository_url_normalizes_supported_urls():
    assert parse_repository_url("https://github.com/psf/requests/") == ("psf", "requests")
    assert parse_repository_url("https://github.com/psf/requests.git") == ("psf", "requests")


@pytest.mark.parametrize("url", ["requests", "https://gitlab.com/a/b", "https://github.com/a"])
def test_parse_repository_url_rejects_invalid_urls(url):
    with pytest.raises(ValueError):
        parse_repository_url(url)


def test_normalizers_return_repository_ready_records():
    assert normalize_repository(FIXTURE["repository"]) == {
        "github_id": 123,
        "full_name": "psf/requests",
        "name": "requests",
        "owner_login": "psf",
        "description": "A simple HTTP library",
        "stars": 10,
        "forks": 2,
        "open_issues": 1,
        "language": "Python",
        "default_branch": "main",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }
    assert normalize_commit(FIXTURE["commit"], 123)["sha"] == "abc123"
    assert normalize_contributor(FIXTURE["contributor"], 123)["login"] == "alice"
    assert normalize_issue(FIXTURE["issue"], 123)["github_id"] == 501
    assert normalize_pull_request(FIXTURE["pull_request"], 123)["number"] == 13