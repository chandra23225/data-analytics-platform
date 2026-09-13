"""GitHub URL parsing, API access, and response normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests


def parse_repository_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("Enter a GitHub repository URL such as https://github.com/owner/repository")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise ValueError("GitHub repository URLs must contain an owner and repository name")
    owner, repository = parts
    repository = re.sub(r"\.git$", "", repository)
    if not owner or not repository:
        raise ValueError("GitHub repository URLs must contain an owner and repository name")
    return owner, repository


class GitHubApiError(RuntimeError):
    def __init__(self, status_code: int, endpoint: str, message: str):
        super().__init__(f"GitHub API error ({status_code}) at {endpoint}: {message}")
        self.status_code = status_code
        self.endpoint = endpoint


@dataclass
class GitHubClient:
    token: str | None = None
    base_url: str = "https://api.github.com"
    timeout: float = 15.0

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json"})
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _get(self, endpoint: str, **params: Any) -> Any:
        response = self.session.get(f"{self.base_url.rstrip('/')}{endpoint}", params=params, timeout=self.timeout)
        if not response.ok:
            try:
                message = response.json().get("message", response.text)
            except ValueError:
                message = response.text
            raise GitHubApiError(response.status_code, endpoint, str(message)[:200])
        return response.json()

    def repository(self, owner: str, repository: str) -> dict[str, Any]:
        return self._get(f"/repos/{owner}/{repository}")

    def commits(self, owner: str, repository: str) -> list[dict[str, Any]]:
        return self._get(f"/repos/{owner}/{repository}/commits", per_page=100)

    def contributors(self, owner: str, repository: str) -> list[dict[str, Any]]:
        return self._get(f"/repos/{owner}/{repository}/contributors", per_page=100)

    def issues(self, owner: str, repository: str) -> list[dict[str, Any]]:
        return self._get(f"/repos/{owner}/{repository}/issues", state="all", per_page=100)

    def pull_requests(self, owner: str, repository: str) -> list[dict[str, Any]]:
        return self._get(f"/repos/{owner}/{repository}/pulls", state="all", per_page=100)


def normalize_repository(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "github_id": data["id"],
        "full_name": data["full_name"],
        "name": data["name"],
        "owner_login": data["owner"]["login"],
        "description": data.get("description"),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "language": data.get("language"),
        "default_branch": data.get("default_branch"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def normalize_commit(data: dict[str, Any], repository_id: int) -> dict[str, Any]:
    commit = data.get("commit", {})
    author = data.get("author") or {}
    commit_author = commit.get("author") or {}
    return {
        "repository_id": repository_id,
        "sha": data["sha"],
        "author_id": author.get("id"),
        "author_login": author.get("login"),
        "message": commit.get("message", ""),
        "committed_at": commit_author.get("date"),
    }


def normalize_contributor(data: dict[str, Any], repository_id: int) -> dict[str, Any]:
    return {
        "repository_id": repository_id,
        "github_id": data.get("id"),
        "login": data.get("login"),
        "contributions": data.get("contributions", 0),
    }


def normalize_issue(data: dict[str, Any], repository_id: int) -> dict[str, Any]:
    user = data.get("user") or {}
    return {
        "repository_id": repository_id,
        "github_id": data["id"],
        "number": data["number"],
        "title": data.get("title", ""),
        "state": data.get("state"),
        "author_login": user.get("login"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def normalize_pull_request(data: dict[str, Any], repository_id: int) -> dict[str, Any]:
    user = data.get("user") or {}
    return {
        "repository_id": repository_id,
        "github_id": data["id"],
        "number": data["number"],
        "title": data.get("title", ""),
        "state": data.get("state"),
        "author_login": user.get("login"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "merged_at": data.get("merged_at"),
    }