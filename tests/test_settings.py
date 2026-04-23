"""Unit tests for `central_server_app_foundation.settings.SettingsStore`.

App-level tests in conter-stats (`tests/unit/test_settings_service.py`)
still cover the public module surface (column catalogs, db_config,
product mapping, …). These tests cover the library class directly:
schema materialisation, the two scopes, JSON convenience helpers,
and the late-binding db_path that tests monkey-patch in the wild.
"""
from __future__ import annotations

import sqlite3

import pytest

from central_server_app_foundation.settings import SettingsStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    s = SettingsStore(db_path=str(tmp_path / "settings.db"))
    s.init_schema()
    return s


# ---------------------------------------------------------------------------
# Schema + connection
# ---------------------------------------------------------------------------

class TestConnection:
    def test_wal_mode_enabled(self, store):
        conn = store._connect()
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode == "wal"
        finally:
            conn.close()

    def test_tables_created_on_connect(self, tmp_path):
        """Schema creation is implicit — the first `_connect()` is enough."""
        s = SettingsStore(db_path=str(tmp_path / "fresh.db"))
        conn = s._connect()
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "global_settings" in tables
            assert "user_preferences" in tables
        finally:
            conn.close()

    def test_init_schema_idempotent(self, store):
        # Calling twice must not raise (CREATE IF NOT EXISTS handles it).
        store.init_schema()
        store.init_schema()


# ---------------------------------------------------------------------------
# User preferences
# ---------------------------------------------------------------------------

class TestUserPref:
    def test_default_when_missing(self, store):
        assert store.get_user_pref("u", "missing", "fallback") == "fallback"

    def test_default_empty_string(self, store):
        assert store.get_user_pref("u", "missing") == ""

    def test_set_and_get(self, store):
        store.set_user_pref("alice", "theme", "dark")
        assert store.get_user_pref("alice", "theme") == "dark"

    def test_upsert_overwrites(self, store):
        store.set_user_pref("alice", "theme", "dark")
        store.set_user_pref("alice", "theme", "light")
        assert store.get_user_pref("alice", "theme") == "light"

    def test_namespace_is_per_user(self, store):
        store.set_user_pref("alice", "theme", "dark")
        store.set_user_pref("bob", "theme", "light")
        assert store.get_user_pref("alice", "theme") == "dark"
        assert store.get_user_pref("bob", "theme") == "light"


# ---------------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------------

class TestGlobal:
    def test_default_when_missing(self, store):
        assert store.get_global("missing", "fallback") == "fallback"

    def test_default_empty_string(self, store):
        assert store.get_global("missing") == ""

    def test_set_and_get(self, store):
        store.set_global("hello", "world")
        assert store.get_global("hello") == "world"

    def test_upsert_overwrites(self, store):
        store.set_global("k", "v1")
        store.set_global("k", "v2")
        assert store.get_global("k") == "v2"

    def test_user_scope_independent(self, store):
        """Same key in both scopes must not collide."""
        store.set_global("theme", "dark")
        store.set_user_pref("alice", "theme", "light")
        assert store.get_global("theme") == "dark"
        assert store.get_user_pref("alice", "theme") == "light"


# ---------------------------------------------------------------------------
# JSON convenience
# ---------------------------------------------------------------------------

class TestJsonHelpers:
    def test_get_default_when_missing(self, store):
        assert store.get_global_json("nope", default=[1, 2]) == [1, 2]

    def test_default_none_by_default(self, store):
        assert store.get_global_json("nope") is None

    def test_set_and_get_list(self, store):
        store.set_global_json("cols", ["id", "name"])
        assert store.get_global_json("cols") == ["id", "name"]

    def test_set_and_get_dict(self, store):
        store.set_global_json("labels", {"id": "ID", "dt": "Date"})
        assert store.get_global_json("labels") == {"id": "ID", "dt": "Date"}

    def test_nested_structure_roundtrip(self, store):
        payload = {
            "charts": [
                {"id": "a", "type": "pie", "col": "model"},
                {"id": "b", "type": "line", "x": "dt", "y": "cycle_time"},
            ],
            "version": 3,
        }
        store.set_global_json("dashboard", payload)
        assert store.get_global_json("dashboard") == payload

    def test_get_json_reads_raw_stored_by_set_global(self, store):
        """`get_global_json` must parse what `set_global` wrote.

        Regression guard for apps that mix the string + JSON APIs.
        """
        import json
        store.set_global("k", json.dumps({"x": 1}))
        assert store.get_global_json("k") == {"x": 1}

    def test_empty_string_value_returns_default(self, store):
        """A stored empty string is treated as absent by `get_global_json`.

        Matches the pre-library contract where `if raw: json.loads(raw)`
        guarded against the "no row" default returning "".
        """
        store.set_global("k", "")
        assert store.get_global_json("k", default="fallback") == "fallback"


# ---------------------------------------------------------------------------
# Late-binding db_path
# ---------------------------------------------------------------------------

class TestLateBindingDbPath:
    def test_callable_db_path_is_re_read(self, tmp_path):
        """Flipping the resolver must target a different DB on next call."""
        db1 = tmp_path / "a.db"
        db2 = tmp_path / "b.db"
        current = {"p": str(db1)}
        s = SettingsStore(db_path=lambda: current["p"])
        s.set_global("where", "db1")
        current["p"] = str(db2)
        # db2 is freshly opened — schema is created on connect; no key yet.
        assert s.get_global("where", "(absent)") == "(absent)"
        # And db1 still has the original value.
        current["p"] = str(db1)
        assert s.get_global("where") == "db1"

    def test_string_db_path_stays_fixed(self, tmp_path):
        """A plain string path must not be re-resolved elsewhere."""
        path = str(tmp_path / "fixed.db")
        s = SettingsStore(db_path=path)
        s.set_global("k", "v")
        # Opening the file directly confirms the path was used.
        with sqlite3.connect(path) as raw:
            row = raw.execute(
                "SELECT value FROM global_settings WHERE key = 'k'"
            ).fetchone()
            assert row[0] == "v"
