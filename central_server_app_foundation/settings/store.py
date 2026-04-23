"""SQLite-backed key/value store for global + per-user settings.

The schema is intentionally tiny — two tables, three columns each:

    global_settings (key PRIMARY KEY, value)
    user_preferences (username, key, value, PRIMARY KEY (username, key))

Every connection opens WAL mode and runs `CREATE TABLE IF NOT
EXISTS` so the first call from any subsystem (settings, workspaces,
wiki, auth — all four services share this DB file by convention)
materialises the tables without an explicit init step. An explicit
`init_schema()` is provided for symmetry with `UserStore` / `WikiStore`
and for apps that prefer to front-load the DDL in their factory.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable


class SettingsStore:
    """Two-scope settings store bound to one SQLite file.

    - `db_path` — absolute SQLite path, or a callable returning one.
      Accepting a callable lets tests monkey-patch an app module-level
      `_DB_PATH` and have every subsequent call see the new value —
      same late-binding pattern as `UserStore` / `WikiStore`.
    """

    def __init__(
        self,
        *,
        db_path: "str | Callable[[], str]",
    ) -> None:
        self._db_path_resolver: Callable[[], str] = (
            db_path if callable(db_path) else (lambda p=db_path: p)
        )

    # ---- connection + schema --------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a fresh WAL-mode connection and materialise the schema.

        Schema creation is idempotent and cheap — it's done on every
        connect so that any subsystem reaching the DB first (auth,
        wiki, settings themselves) finds its tables ready without
        caring about init order.
        """
        conn = sqlite3.connect(self._db_path_resolver())
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS user_preferences ("
            "  username TEXT NOT NULL,"
            "  key TEXT NOT NULL,"
            "  value TEXT NOT NULL,"
            "  PRIMARY KEY (username, key)"
            ")"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS global_settings ("
            "  key TEXT PRIMARY KEY,"
            "  value TEXT NOT NULL"
            ")"
        )
        return conn

    def init_schema(self) -> None:
        """Explicit materialisation hook. No-op if the tables already exist."""
        self._connect().close()

    # ---- user preferences ------------------------------------------------

    def get_user_pref(self, username: str, key: str, default: str = "") -> str:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE username = ? AND key = ?",
                (username, key),
            ).fetchone()
            return row[0] if row else default
        finally:
            conn.close()

    def set_user_pref(self, username: str, key: str, value: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO user_preferences (username, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT(username, key) DO UPDATE SET value = excluded.value",
                (username, key, value),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- global settings -------------------------------------------------

    def get_global(self, key: str, default: str = "") -> str:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM global_settings WHERE key = ?", (key,)
            ).fetchone()
            return row[0] if row else default
        finally:
            conn.close()

    def set_global(self, key: str, value: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO global_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- JSON convenience ------------------------------------------------

    def get_global_json(self, key: str, default: Any = None) -> Any:
        """Return the JSON-decoded value at `key`, or `default` if absent.

        Domain helpers in apps look like
        `json.loads(get_global("charts_test", "")) or []` seven times
        over — this method replaces the pattern with a single call.
        """
        raw = self.get_global(key, "")
        if not raw:
            return default
        return json.loads(raw)

    def set_global_json(self, key: str, value: Any) -> None:
        """Encode `value` as JSON and store it under `key`."""
        self.set_global(key, json.dumps(value))
