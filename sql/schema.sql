PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS repositories (
    github_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    owner_login TEXT NOT NULL,
    description TEXT,
    stars INTEGER NOT NULL DEFAULT 0,
    forks INTEGER NOT NULL DEFAULT 0,
    open_issues INTEGER NOT NULL DEFAULT 0,
    language TEXT,
    default_branch TEXT,
    created_at TEXT,
    updated_at TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS commits (
    repository_id INTEGER NOT NULL REFERENCES repositories(github_id) ON DELETE CASCADE,
    sha TEXT NOT NULL,
    author_id INTEGER,
    author_login TEXT,
    message TEXT NOT NULL,
    committed_at TEXT,
    PRIMARY KEY (repository_id, sha)
);

CREATE TABLE IF NOT EXISTS contributors (
    repository_id INTEGER NOT NULL REFERENCES repositories(github_id) ON DELETE CASCADE,
    github_id INTEGER,
    login TEXT NOT NULL,
    contributions INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (repository_id, login)
);

CREATE TABLE IF NOT EXISTS issues (
    repository_id INTEGER NOT NULL REFERENCES repositories(github_id) ON DELETE CASCADE,
    github_id INTEGER NOT NULL,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    state TEXT,
    author_login TEXT,
    created_at TEXT,
    updated_at TEXT,
    PRIMARY KEY (repository_id, github_id)
);

CREATE TABLE IF NOT EXISTS pull_requests (
    repository_id INTEGER NOT NULL REFERENCES repositories(github_id) ON DELETE CASCADE,
    github_id INTEGER NOT NULL,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    state TEXT,
    author_login TEXT,
    created_at TEXT,
    updated_at TEXT,
    merged_at TEXT,
    PRIMARY KEY (repository_id, github_id)
);

CREATE INDEX IF NOT EXISTS idx_commits_repository_date ON commits(repository_id, committed_at);
CREATE INDEX IF NOT EXISTS idx_issues_repository_date ON issues(repository_id, created_at);
CREATE INDEX IF NOT EXISTS idx_pull_requests_repository_date ON pull_requests(repository_id, created_at);