"""Per-user SQLite data store. Persistent data stays outside versioned releases."""
from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')), created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL, document TEXT NOT NULL, thumbnail TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_project_owner_updated ON projects(owner_id,updated_at DESC);
CREATE TABLE IF NOT EXISTS publications (
  token TEXT PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  file_name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_publications_owner ON publications(owner_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_publications_recent ON publications(created_at DESC,token DESC);
CREATE TABLE IF NOT EXISTS provider_keys (
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL, ciphertext BLOB NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(owner_id,provider)
);
'''

def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA busy_timeout=15000')
    return con

def init(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as con:
        con.execute('PRAGMA journal_mode=WAL')
        con.executescript(SCHEMA)
        # Add roles to established v0.1.x databases without touching existing passwords/projects.
        columns={row[1] for row in con.execute('PRAGMA table_info(users)')}
        if 'role' not in columns:
            con.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin'))")
