"""Unit tests for `conter_app_base.auth.UserStore`.

App-level tests in conter-stats (`tests/unit/test_auth_service.py`)
still verify the public module surface (`authenticate`, `create_user`,
…). These tests cover the library class directly: constructor
parameters, late-binding db_path, the translator callable, and the
edge cases that only matter if multiple apps consume it with
different bootstrap admins / role taxonomies.
"""
from __future__ import annotations

import pytest

from conter_app_base.auth import UserStore, VALID_ROLES, can_publish


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    """A fresh UserStore bound to a throw-away SQLite file."""
    db = tmp_path / "users.db"
    s = UserStore(
        db_path=str(db),
        admin_user="boss",
        admin_pass="bosspass",
    )
    s.init_schema()
    return s


# ---------------------------------------------------------------------------
# Constants / stateless helpers
# ---------------------------------------------------------------------------

class TestRoleTaxonomy:
    def test_valid_roles_exposed(self):
        assert VALID_ROLES == ("operator", "supervisor", "admin")

    @pytest.mark.parametrize("role,expected", [
        ("admin", True),
        ("supervisor", True),
        ("operator", False),
        ("", False),
        ("unknown", False),
    ])
    def test_can_publish(self, role, expected):
        assert can_publish(role) is expected


# ---------------------------------------------------------------------------
# init_schema
# ---------------------------------------------------------------------------

class TestInitSchema:
    def test_seeds_admin(self, store):
        users = store.list_users()
        admin = next((u for u in users if u["username"] == "boss"), None)
        assert admin is not None
        assert admin["is_admin"] is True
        assert admin["role"] == "admin"

    def test_idempotent(self, tmp_path):
        """Calling init_schema twice must not duplicate the bootstrap admin."""
        s = UserStore(
            db_path=str(tmp_path / "u.db"),
            admin_user="boss",
            admin_pass="p",
        )
        s.init_schema()
        s.init_schema()
        assert sum(1 for u in s.list_users() if u["username"] == "boss") == 1

    def test_seeded_admin_can_authenticate(self, store):
        user = store.authenticate("boss", "bosspass")
        assert user == {"username": "boss", "is_admin": True, "role": "admin"}


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_wrong_password_returns_none(self, store):
        assert store.authenticate("boss", "nope") is None

    def test_unknown_user_returns_none(self, store):
        assert store.authenticate("ghost", "whatever") is None

    def test_created_user_authenticates(self, store):
        store.create_user("alice", "alicepw")
        user = store.authenticate("alice", "alicepw")
        assert user == {"username": "alice", "is_admin": False,
                        "role": "operator"}


# ---------------------------------------------------------------------------
# create_user / delete_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_creates_with_operator_role(self, store):
        store.create_user("alice", "pw")
        assert store.get_role("alice") == "operator"

    def test_duplicate_raises(self, store):
        store.create_user("alice", "pw")
        with pytest.raises(ValueError, match="already exists"):
            store.create_user("alice", "pw2")


class TestDeleteUser:
    def test_delete_regular_user(self, store):
        store.create_user("alice", "pw")
        store.delete_user("alice")
        assert store.authenticate("alice", "pw") is None

    def test_cannot_delete_bootstrap_admin(self, store):
        with pytest.raises(ValueError, match="Cannot delete"):
            store.delete_user("boss")

    def test_deleting_unknown_is_noop(self, store):
        # SQL DELETE with no matching row is fine; the API doesn't promise
        # an error here. Regression canary.
        store.delete_user("nobody")


# ---------------------------------------------------------------------------
# change_password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_changes_and_old_stops_working(self, store):
        store.create_user("alice", "old")
        store.change_password("alice", "new")
        assert store.authenticate("alice", "old") is None
        assert store.authenticate("alice", "new") is not None


# ---------------------------------------------------------------------------
# set_role / get_role
# ---------------------------------------------------------------------------

class TestSetRole:
    def test_promote_to_supervisor(self, store):
        store.create_user("alice", "pw")
        store.set_role("alice", "supervisor")
        assert store.get_role("alice") == "supervisor"

    def test_promote_to_admin_sets_is_admin(self, store):
        store.create_user("alice", "pw")
        store.set_role("alice", "admin")
        user = store.authenticate("alice", "pw")
        assert user["is_admin"] is True

    def test_invalid_role_rejected(self, store):
        store.create_user("alice", "pw")
        with pytest.raises(ValueError, match="Invalid role"):
            store.set_role("alice", "god")

    def test_cannot_demote_bootstrap_admin(self, store):
        with pytest.raises(ValueError, match="Cannot demote"):
            store.set_role("boss", "operator")

    def test_bootstrap_admin_can_stay_admin(self, store):
        # Re-setting to the same role must not trip the demotion guard.
        store.set_role("boss", "admin")

    def test_unknown_user_rejected(self, store):
        with pytest.raises(ValueError, match="not found"):
            store.set_role("ghost", "supervisor")


class TestGetRole:
    def test_unknown_user_defaults_to_operator(self, store):
        assert store.get_role("ghost") == "operator"


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_sorted_alphabetically(self, store):
        store.create_user("zz", "p")
        store.create_user("aa", "p")
        names = [u["username"] for u in store.list_users()]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# Late-binding db_path
# ---------------------------------------------------------------------------

class TestDbPathCallable:
    def test_callable_db_path_is_re_read_per_call(self, tmp_path):
        """Tests monkeypatch the module-level _DB_PATH and rely on the
        store re-resolving on each call."""
        db1 = tmp_path / "a.db"
        db2 = tmp_path / "b.db"
        current = {"path": str(db1)}

        s = UserStore(
            db_path=lambda: current["path"],
            admin_user="boss",
            admin_pass="p",
        )
        s.init_schema()
        s.create_user("alice", "pw")

        # Flip the path — the next call must target a different DB.
        current["path"] = str(db2)
        s.init_schema()  # creates fresh schema + seeds boss in db2
        assert s.authenticate("alice", "pw") is None, (
            "store kept using the old db_path"
        )


# ---------------------------------------------------------------------------
# Custom role taxonomy
# ---------------------------------------------------------------------------

class TestCustomRoles:
    def test_accepts_custom_role_tuple(self, tmp_path):
        s = UserStore(
            db_path=str(tmp_path / "u.db"),
            admin_user="boss",
            admin_pass="p",
            valid_roles=("reader", "writer", "admin"),
        )
        s.init_schema()
        s.create_user("alice", "pw")
        s.set_role("alice", "reader")
        assert s.get_role("alice") == "reader"

    def test_custom_taxonomy_rejects_default_roles(self, tmp_path):
        """If an app narrows the taxonomy, the old names must be gone."""
        s = UserStore(
            db_path=str(tmp_path / "u.db"),
            admin_user="boss",
            admin_pass="p",
            valid_roles=("reader", "writer", "admin"),
        )
        s.init_schema()
        s.create_user("alice", "pw")
        with pytest.raises(ValueError, match="Invalid role"):
            s.set_role("alice", "supervisor")


# ---------------------------------------------------------------------------
# Translator callable
# ---------------------------------------------------------------------------

class TestTranslator:
    def test_custom_translator_wraps_error_messages(self, tmp_path):
        def shout(s, **kw):
            return ("!! " + (s % kw if kw else s) + " !!").upper()

        s = UserStore(
            db_path=str(tmp_path / "u.db"),
            admin_user="boss",
            admin_pass="p",
            gettext=shout,
        )
        s.init_schema()
        with pytest.raises(ValueError, match="CANNOT DELETE"):
            s.delete_user("boss")

    def test_default_translator_formats_kwargs(self, store):
        """Even without i18n, `%(name)s` placeholders must be filled in."""
        store.create_user("alice", "pw")
        with pytest.raises(ValueError, match='User "alice" already exists'):
            store.create_user("alice", "pw2")
