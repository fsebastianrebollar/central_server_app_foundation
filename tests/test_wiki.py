"""Unit tests for `central_server_app_foundation.wiki`.

App-level tests in conter-stats (`tests/unit/test_wiki_service.py`)
still cover the public module surface — these tests hit the library
class directly: constructor wiring, late-binding db_path and
uploads_dir, the locale resolver, the translator callable, and the
edge cases that only matter when multiple apps consume the same
store (custom translators, varying locales, alternate uploads dirs).
"""
from __future__ import annotations

import io
import os

import pytest

from central_server_app_foundation.wiki import (
    ROLE_RANK,
    VALID_MIN_ROLES,
    WikiStore,
    render_markdown,
    safe_upload_name,
    slugify,
    user_can_see,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    s = WikiStore(
        db_path=str(tmp_path / "wiki.db"),
        uploads_dir=str(uploads),
    )
    s.init_schema()
    return s


class _FakeFile:
    """Minimal werkzeug FileStorage lookalike for save_upload tests."""

    def __init__(self, filename: str, payload: bytes = b"x"):
        self.filename = filename
        self._payload = payload

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(self._payload)


# ---------------------------------------------------------------------------
# Stateless helpers
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_accents_and_punctuation(self):
        assert slugify("¿Qué pasa, amigo?") == "que-pasa-amigo"

    @pytest.mark.parametrize("value", ["", "   ", "!!!", "///"])
    def test_empty_fallback(self, value):
        assert slugify(value) == "page"


class TestRoleHelpers:
    def test_role_rank_order(self):
        assert ROLE_RANK["guest"] < ROLE_RANK["operator"] < ROLE_RANK["supervisor"] < ROLE_RANK["admin"]

    def test_valid_min_roles_set(self):
        # Operators cannot restrict pages; only supervisor/admin gating exists.
        assert VALID_MIN_ROLES == {None, "supervisor", "admin"}

    @pytest.mark.parametrize("min_role,user_role,expected", [
        (None, "guest", True),
        (None, None, True),
        ("admin", "admin", True),
        ("admin", "supervisor", False),
        ("admin", "operator", False),
        ("supervisor", "admin", True),
        ("supervisor", "supervisor", True),
        ("supervisor", "operator", False),
    ])
    def test_user_can_see(self, min_role, user_role, expected):
        assert user_can_see(min_role, user_role) is expected


class TestSafeUploadName:
    def test_strips_path(self):
        assert safe_upload_name("/etc/passwd") == "passwd"

    def test_replaces_unsafe_chars(self):
        assert safe_upload_name("my file (1).png") == "my_file_1_.png"

    def test_empty_fallback(self):
        assert safe_upload_name("") == "image"
        assert safe_upload_name("...") == "image"


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_empty_returns_empty(self):
        assert render_markdown("") == ""

    def test_heading_and_list(self):
        html = render_markdown("# Hi\n\n- a\n- b\n")
        assert "<h1" in html and "<li>a</li>" in html and "<li>b</li>" in html

    def test_fenced_code(self):
        html = render_markdown("```\ncode\n```")
        assert "<pre>" in html and "<code>" in html

    def test_tables(self):
        html = render_markdown("| a | b |\n|---|---|\n| 1 | 2 |\n")
        assert "<table>" in html

    def test_url_prefix_rewrites_uploads(self):
        md = "![alt](/api/wiki/uploads/foo.png)"
        html = render_markdown(md, url_prefix="/services/app")
        assert 'src="/services/app/api/wiki/uploads/foo.png"' in html

    def test_prefix_trailing_slash_is_trimmed(self):
        html = render_markdown(
            "![alt](/api/wiki/uploads/foo.png)",
            url_prefix="/services/app/",
        )
        assert 'src="/services/app/api/wiki/uploads/foo.png"' in html

    def test_empty_prefix_is_noop(self):
        html = render_markdown("![alt](/api/wiki/uploads/foo.png)")
        assert 'src="/api/wiki/uploads/foo.png"' in html


# ---------------------------------------------------------------------------
# Schema + CRUD
# ---------------------------------------------------------------------------

class TestInitSchema:
    def test_idempotent(self, store):
        store.init_schema()  # second call must not crash on existing table.
        assert store.is_empty() is True


class TestCreatePage:
    def test_creates_root(self, store):
        p = store.create_page(title="My page", content="# hi")
        assert p["id"] > 0
        assert p["slug"] == "my-page"
        assert p["title"] == "My page"
        assert p["parent_id"] is None

    def test_requires_title(self, store):
        with pytest.raises(ValueError, match="title required"):
            store.create_page(title="   ")

    def test_slug_collision_suffixes(self, store):
        a = store.create_page(title="Page")
        b = store.create_page(title="Page")
        c = store.create_page(title="Page")
        assert {a["slug"], b["slug"], c["slug"]} == {"page", "page-2", "page-3"}

    def test_sort_order_monotonically_increases(self, store):
        a = store.create_page(title="A")
        b = store.create_page(title="B")
        c = store.create_page(title="C")
        assert a["sort_order"] < b["sort_order"] < c["sort_order"]

    def test_child_of_parent(self, store):
        root = store.create_page(title="Root")
        child = store.create_page(title="Child", parent_id=root["id"])
        assert child["parent_id"] == root["id"]

    def test_missing_parent_raises(self, store):
        with pytest.raises(ValueError, match="parent not found"):
            store.create_page(title="x", parent_id=9999)

    def test_invalid_min_role_rejected(self, store):
        with pytest.raises(ValueError, match="invalid min_role"):
            store.create_page(title="x", min_role="hacker")

    def test_translations_persisted(self, store):
        p = store.create_page(
            title="Hello", content="# hi",
            title_es="Hola", content_es="# hola",
            title_de="Hallo", content_de="# hallo",
        )
        assert p["id"] > 0


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

class TestGetPage:
    def test_returns_dict_or_none(self, store):
        p = store.create_page(title="T", content="body")
        assert store.get_page(p["id"])["title"] == "T"
        assert store.get_page(99999) is None


class TestListTree:
    def test_nested_tree(self, store):
        root = store.create_page(title="Root")
        c1 = store.create_page(title="C1", parent_id=root["id"])
        store.create_page(title="C2", parent_id=root["id"])
        store.create_page(title="GC", parent_id=c1["id"])
        tree = store.list_tree()
        assert len(tree) == 1
        assert tree[0]["title"] == "Root"
        assert len(tree[0]["children"]) == 2

    def test_role_filters_subtree(self, store):
        # Admin-only root hides its whole subtree from an operator.
        parent = store.create_page(title="Secret", min_role="admin")
        store.create_page(title="Child", parent_id=parent["id"])
        as_op = store.list_tree(user_role="operator")
        as_admin = store.list_tree(user_role="admin")
        assert [n["title"] for n in as_op] == []
        assert [n["title"] for n in as_admin] == ["Secret"]

    def test_user_role_none_shows_everything(self, store):
        store.create_page(title="Secret", min_role="admin")
        assert len(store.list_tree()) == 1


class TestGetFirstPage:
    def test_respects_role(self, store):
        store.create_page(title="A", min_role="admin")
        store.create_page(title="B")  # visible to everyone
        assert store.get_first_page(user_role="operator")["title"] == "B"
        # An admin sees A first because it was inserted first (lower sort_order).
        assert store.get_first_page(user_role="admin")["title"] == "A"

    def test_none_when_wiki_empty(self, store):
        assert store.get_first_page() is None


class TestBreadcrumb:
    def test_chain_from_root(self, store):
        a = store.create_page(title="A")
        b = store.create_page(title="B", parent_id=a["id"])
        c = store.create_page(title="C", parent_id=b["id"])
        chain = store.get_breadcrumb(c["id"])
        assert [x["title"] for x in chain] == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class TestUpdatePage:
    def test_changes_title_and_slug(self, store):
        p = store.create_page(title="First")
        upd = store.update_page(p["id"], title="Second")
        assert upd["title"] == "Second" and upd["slug"] == "second"

    def test_content_only_does_not_touch_slug(self, store):
        p = store.create_page(title="Stable")
        upd = store.update_page(p["id"], content="new")
        assert upd["slug"] == "stable" and upd["content"] == "new"

    def test_min_role_unset_keeps_existing(self, store):
        p = store.create_page(title="P", min_role="admin")
        upd = store.update_page(p["id"], title="P2")  # no min_role kwarg
        assert upd["min_role"] == "admin"

    def test_min_role_none_clears(self, store):
        p = store.create_page(title="P", min_role="admin")
        upd = store.update_page(p["id"], min_role=None)
        assert upd["min_role"] is None

    def test_missing_page_raises(self, store):
        with pytest.raises(ValueError, match="page not found"):
            store.update_page(9999, title="x")


class TestDeletePage:
    def test_cascades_to_children(self, store):
        root = store.create_page(title="Root")
        child = store.create_page(title="Child", parent_id=root["id"])
        grand = store.create_page(title="Grand", parent_id=child["id"])
        assert store.delete_page(root["id"]) is True
        assert store.get_page(child["id"]) is None
        assert store.get_page(grand["id"]) is None

    def test_delete_missing_returns_false(self, store):
        assert store.delete_page(9999) is False


class TestMovePage:
    def test_reparent(self, store):
        a = store.create_page(title="A")
        b = store.create_page(title="B")
        moved = store.move_page(b["id"], new_parent_id=a["id"])
        assert moved["parent_id"] == a["id"]

    def test_cycle_rejected(self, store):
        a = store.create_page(title="A")
        b = store.create_page(title="B", parent_id=a["id"])
        with pytest.raises(ValueError, match="cycle"):
            store.move_page(a["id"], new_parent_id=b["id"])

    def test_self_parent_rejected(self, store):
        a = store.create_page(title="A")
        with pytest.raises(ValueError, match="itself"):
            store.move_page(a["id"], new_parent_id=a["id"])


# ---------------------------------------------------------------------------
# Seed / backfill
# ---------------------------------------------------------------------------

SEED_ARTICLES = [
    {
        "key": "welcome",
        "parent": None,
        "title": {"en": "Welcome", "es": "Bienvenido", "de": "Willkommen"},
        "content": {"en": "# Welcome", "es": "# Bienvenido", "de": "# Willkommen"},
        "min_role": None,
    },
    {
        "key": "admin",
        "parent": "welcome",
        "title": {"en": "Admin", "es": "Admin", "de": "Admin"},
        "content": {"en": "# admin", "es": "# admin", "de": "# admin"},
        "min_role": "admin",
    },
]


class TestSeed:
    def test_seeds_on_empty_wiki(self, store):
        wrote = store.seed(SEED_ARTICLES)
        assert wrote is True
        tree = store.list_tree()
        assert len(tree) == 1
        assert tree[0]["title"] == "Welcome"
        assert tree[0]["children"][0]["title"] == "Admin"

    def test_non_empty_wiki_backfills_translations(self, store):
        # Pre-existing row without translations — simulates a legacy DB.
        store.create_page(title="Welcome", content="# Welcome")
        wrote = store.seed(SEED_ARTICLES)
        assert wrote is True
        # Backfill should now fill in ES columns.
        page_id = store.list_tree()[0]["id"]
        row_es = _read_raw(store, page_id, "title_es")
        assert row_es == "Bienvenido"

    def test_backfill_idempotent(self, store):
        store.create_page(title="Welcome", content="# Welcome")
        store.seed(SEED_ARTICLES)  # fills translations
        wrote = store.seed(SEED_ARTICLES)  # nothing left to fill
        assert wrote is False


def _read_raw(store, page_id, col):
    conn = store._connect()
    try:
        return conn.execute(
            f"SELECT {col} FROM wiki_pages WHERE id = ?", (page_id,)
        ).fetchone()[0]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------------

class TestLocalisation:
    def test_es_locale_returns_spanish_title(self, tmp_path):
        current = {"loc": "en"}
        s = WikiStore(
            db_path=str(tmp_path / "w.db"),
            uploads_dir=str(tmp_path),
            locale_resolver=lambda: current["loc"],
        )
        s.init_schema()
        s.create_page(title="Hello", title_es="Hola", content_es="# hola")
        current["loc"] = "es"
        page = s.list_tree()[0]
        assert page["title"] == "Hola"

    def test_locale_falls_back_to_english_when_translation_missing(self, tmp_path):
        s = WikiStore(
            db_path=str(tmp_path / "w.db"),
            uploads_dir=str(tmp_path),
            locale_resolver=lambda: "es",
        )
        s.init_schema()
        p = s.create_page(title="Hello", content="# hi")  # no ES values
        fetched = s.get_page(p["id"])
        assert fetched["title"] == "Hello"
        assert fetched["content"] == "# hi"


# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------

class TestSaveUpload:
    def test_saves_png(self, store, tmp_path):
        result = store.save_upload(_FakeFile("cat.png", b"binary"))
        assert result["filename"].endswith(".png")
        assert result["url"].startswith("/api/wiki/uploads/")
        # File actually landed in uploads_dir.
        full = os.path.join(tmp_path / "uploads", result["filename"])
        assert os.path.isfile(full)

    def test_rejects_unknown_extension(self, store):
        with pytest.raises(ValueError, match="not allowed"):
            store.save_upload(_FakeFile("malware.exe"))

    def test_extensionless_rejected(self, store):
        with pytest.raises(ValueError, match="not allowed"):
            store.save_upload(_FakeFile("noext"))

    def test_special_chars_sanitised_in_filename(self, store):
        result = store.save_upload(_FakeFile("my file (1).png"))
        # No spaces or parens in the saved filename.
        assert " " not in result["filename"]
        assert "(" not in result["filename"]


class TestUploadPath:
    def test_rejects_traversal(self, store):
        assert store.upload_path("../x") is None
        assert store.upload_path("/abs/path") is None

    def test_rejects_missing(self, store):
        assert store.upload_path("nope.png") is None

    def test_returns_absolute_path_when_file_exists(self, store, tmp_path):
        result = store.save_upload(_FakeFile("cat.png"))
        full = store.upload_path(result["filename"])
        assert full is not None and os.path.isfile(full)


# ---------------------------------------------------------------------------
# Late-binding path resolvers
# ---------------------------------------------------------------------------

class TestLateBindingResolvers:
    def test_db_path_callable_is_re_read(self, tmp_path):
        """Flipping the resolver must target a different DB on next call."""
        db1 = tmp_path / "a.db"
        db2 = tmp_path / "b.db"
        current = {"db": str(db1)}
        s = WikiStore(
            db_path=lambda: current["db"],
            uploads_dir=str(tmp_path),
        )
        s.init_schema()
        s.create_page(title="only-in-db1")
        current["db"] = str(db2)
        s.init_schema()
        assert s.list_tree() == []

    def test_uploads_dir_callable_is_re_read(self, tmp_path):
        dir1 = tmp_path / "one"
        dir2 = tmp_path / "two"
        dir1.mkdir()
        dir2.mkdir()
        current = {"up": str(dir1)}
        s = WikiStore(
            db_path=str(tmp_path / "w.db"),
            uploads_dir=lambda: current["up"],
        )
        s.init_schema()
        r1 = s.save_upload(_FakeFile("a.png"))
        assert os.path.isfile(os.path.join(dir1, r1["filename"]))
        current["up"] = str(dir2)
        r2 = s.save_upload(_FakeFile("b.png"))
        assert os.path.isfile(os.path.join(dir2, r2["filename"]))


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------

class TestTranslator:
    def test_custom_translator_wraps_messages(self, tmp_path):
        def shout(s, **kw):
            return ("!! " + (s % kw if kw else s) + " !!").upper()

        s = WikiStore(
            db_path=str(tmp_path / "w.db"),
            uploads_dir=str(tmp_path),
            gettext=shout,
        )
        s.init_schema()
        with pytest.raises(ValueError, match="TITLE REQUIRED"):
            s.create_page(title="   ")
