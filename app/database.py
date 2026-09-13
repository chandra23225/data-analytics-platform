"""SQLite storage for normalized GitHub repository snapshots."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connection(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(SCHEMA_PATH.read_text())

    def upsert_repository(self, repository: dict) -> None:
        fields = [
            "github_id", "full_name", "name", "owner_login", "description", "stars",
            "forks", "open_issues", "language", "default_branch", "created_at", "updated_at",
        ]
        values = [repository.get(field) for field in fields]
        values.append(datetime.now(timezone.utc).isoformat())
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO repositories (
                    github_id, full_name, name, owner_login, description, stars, forks,
                    open_issues, language, default_branch, created_at, updated_at, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(github_id) DO UPDATE SET
                    full_name=excluded.full_name, name=excluded.name, owner_login=excluded.owner_login,
                    description=excluded.description, stars=excluded.stars, forks=excluded.forks,
                    open_issues=excluded.open_issues, language=excluded.language,
                    default_branch=excluded.default_branch, created_at=excluded.created_at,
                    updated_at=excluded.updated_at, fetched_at=excluded.fetched_at""",
                values,
            )

    def replace_repository_snapshot(
        self,
        repository: dict,
        commits: Iterable[dict],
        contributors: Iterable[dict],
        issues: Iterable[dict],
        pull_requests: Iterable[dict],
    ) -> None:
        self.initialize()
        with self.connection() as connection:
            self._upsert_repository(connection, repository)
            repository_id = repository["github_id"]
            for table in ("commits", "contributors", "issues", "pull_requests"):
                connection.execute(f"DELETE FROM {table} WHERE repository_id = ?", (repository_id,))
            connection.executemany(
                "INSERT INTO commits (repository_id, sha, author_id, author_login, message, committed_at) VALUES (?, ?, ?, ?, ?, ?)",
                [(item["repository_id"], item["sha"], item.get("author_id"), item.get("author_login"), item["message"], item.get("committed_at")) for item in commits],
            )
            connection.executemany(
                "INSERT INTO contributors (repository_id, github_id, login, contributions) VALUES (?, ?, ?, ?)",
                [(item["repository_id"], item.get("github_id"), item["login"], item.get("contributions", 0)) for item in contributors],
            )
            connection.executemany(
                "INSERT INTO issues (repository_id, github_id, number, title, state, author_login, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(item["repository_id"], item["github_id"], item["number"], item["title"], item.get("state"), item.get("author_login"), item.get("created_at"), item.get("updated_at")) for item in issues],
            )
            connection.executemany(
                "INSERT INTO pull_requests (repository_id, github_id, number, title, state, author_login, created_at, updated_at, merged_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(item["repository_id"], item["github_id"], item["number"], item["title"], item.get("state"), item.get("author_login"), item.get("created_at"), item.get("updated_at"), item.get("merged_at")) for item in pull_requests],
            )

    @staticmethod
    def _upsert_repository(connection: sqlite3.Connection, repository: dict) -> None:
        connection.execute(
            """INSERT INTO repositories (
                github_id, full_name, name, owner_login, description, stars, forks,
                open_issues, language, default_branch, created_at, updated_at, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(github_id) DO UPDATE SET
                full_name=excluded.full_name, name=excluded.name, owner_login=excluded.owner_login,
                description=excluded.description, stars=excluded.stars, forks=excluded.forks,
                open_issues=excluded.open_issues, language=excluded.language,
                default_branch=excluded.default_branch, created_at=excluded.created_at,
                updated_at=excluded.updated_at, fetched_at=excluded.fetched_at""",
            (
                repository["github_id"], repository["full_name"], repository["name"], repository["owner_login"],
                repository.get("description"), repository.get("stars", 0), repository.get("forks", 0),
                repository.get("open_issues", 0), repository.get("language"), repository.get("default_branch"),
                repository.get("created_at"), repository.get("updated_at"), datetime.now(timezone.utc).isoformat(),
            ),
        )