"""Parameterized SQL analytics for dashboard views."""

from __future__ import annotations

import sqlite3

import pandas as pd


def _placeholders(values: list[int]) -> str:
    return ", ".join("?" for _ in values)


def get_overview(connection: sqlite3.Connection, repository_ids: list[int]) -> pd.DataFrame:
    if not repository_ids:
        return pd.DataFrame(columns=["repository_count", "stars", "forks", "open_issues", "commits", "contributors", "issues", "pull_requests"])
    placeholders = _placeholders(repository_ids)
    query = f"""
        SELECT COUNT(*) AS repository_count,
               COALESCE(SUM(r.stars), 0) AS stars,
               COALESCE(SUM(r.forks), 0) AS forks,
               COALESCE(SUM(r.open_issues), 0) AS open_issues,
               (SELECT COUNT(*) FROM commits WHERE repository_id IN ({placeholders})) AS commits,
               (SELECT COUNT(*) FROM contributors WHERE repository_id IN ({placeholders})) AS contributors,
               (SELECT COUNT(*) FROM issues WHERE repository_id IN ({placeholders})) AS issues,
               (SELECT COUNT(*) FROM pull_requests WHERE repository_id IN ({placeholders})) AS pull_requests
        FROM repositories r WHERE r.github_id IN ({placeholders})
    """
    parameters = repository_ids * 5
    return pd.read_sql_query(query, connection, params=parameters)


def get_activity_trend(connection: sqlite3.Connection, repository_ids: list[int], start_date: str, end_date: str) -> pd.DataFrame:
    if not repository_ids:
        return pd.DataFrame(columns=["activity_date", "commits", "issues", "pull_requests"])
    placeholders = _placeholders(repository_ids)
    query = f"""
        WITH dates AS (
            SELECT substr(committed_at, 1, 10) AS activity_date, COUNT(*) AS commits
            FROM commits WHERE repository_id IN ({placeholders}) AND substr(committed_at, 1, 10) >= ? AND substr(committed_at, 1, 10) <= ?
            GROUP BY activity_date
            UNION SELECT substr(created_at, 1, 10), 0 FROM issues WHERE repository_id IN ({placeholders}) AND substr(created_at, 1, 10) >= ? AND substr(created_at, 1, 10) <= ?
            UNION SELECT substr(created_at, 1, 10), 0 FROM pull_requests WHERE repository_id IN ({placeholders}) AND substr(created_at, 1, 10) >= ? AND substr(created_at, 1, 10) <= ?
        ), activity AS (
            SELECT activity_date, SUM(commits) AS commits FROM dates GROUP BY activity_date
        )
        SELECT activity_date, commits,
               (SELECT COUNT(*) FROM issues i WHERE i.repository_id IN ({placeholders}) AND substr(i.created_at, 1, 10) = activity.activity_date) AS issues,
               (SELECT COUNT(*) FROM pull_requests p WHERE p.repository_id IN ({placeholders}) AND substr(p.created_at, 1, 10) = activity.activity_date) AS pull_requests
        FROM activity ORDER BY activity_date
    """
    parameters = repository_ids + [start_date, end_date] + repository_ids + [start_date, end_date] + repository_ids + [start_date, end_date] + repository_ids + repository_ids
    return pd.read_sql_query(query, connection, params=parameters)


def get_contributor_ranking(connection: sqlite3.Connection, repository_ids: list[int]) -> pd.DataFrame:
    if not repository_ids:
        return pd.DataFrame(columns=["login", "contributions"])
    placeholders = _placeholders(repository_ids)
    return pd.read_sql_query(
        f"SELECT login, SUM(contributions) AS contributions FROM contributors WHERE repository_id IN ({placeholders}) GROUP BY login ORDER BY contributions DESC, login",
        connection,
        params=repository_ids,
    )


def get_repository_comparison(connection: sqlite3.Connection, repository_ids: list[int]) -> pd.DataFrame:
    if not repository_ids:
        return pd.DataFrame(columns=["full_name", "stars", "forks", "commits", "contributors", "issues", "pull_requests"])
    placeholders = _placeholders(repository_ids)
    query = f"""
        SELECT r.full_name, r.stars, r.forks,
               (SELECT COUNT(*) FROM commits c WHERE c.repository_id = r.github_id) AS commits,
               (SELECT COUNT(*) FROM contributors c WHERE c.repository_id = r.github_id) AS contributors,
               (SELECT COUNT(*) FROM issues i WHERE i.repository_id = r.github_id) AS issues,
               (SELECT COUNT(*) FROM pull_requests p WHERE p.repository_id = r.github_id) AS pull_requests
        FROM repositories r WHERE r.github_id IN ({placeholders}) ORDER BY r.stars DESC, r.full_name
    """
    return pd.read_sql_query(query, connection, params=repository_ids)