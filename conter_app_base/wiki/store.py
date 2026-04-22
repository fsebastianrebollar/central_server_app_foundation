"""SQLite-backed wiki store — tree + localisation + uploads.

`WikiStore` owns:

- schema migration (additive, safe on legacy DBs with older columns),
- CRUD on `wiki_pages` with unique-slug-per-parent enforcement,
- locale-aware reads (title/content with ES/DE columns + EN fallback),
- `seed(articles)` that takes a per-app article list and fills an
  empty wiki, or backfills missing translation columns on an existing
  wiki (idempotent).
- image uploads: `save_upload(file_storage) -> {url, filename}` and
  `upload_path(filename) -> str | None` with path-traversal protection.

The store resolves `db_path` and `uploads_dir` on every call via
late-binding callables so tests can monkey-patch the module-level path
names and have every subsequent call see the new value — preserving
the conter-stats pattern where `_DB_PATH` and `UPLOADS_DIR` live on
the app module and tests swap them in a fixture.
"""
from __future__ import annotations

import os
import sqlite3
import time
from typing import Callable, Optional

from conter_app_base.wiki.utils import (
    VALID_MIN_ROLES,
    safe_upload_name,
    slugify,
    user_can_see,
)


_ALLOWED_IMG_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def _default_gettext(string: str, **variables) -> str:
    """Identity translator (matches `flask_babel.gettext`'s signature)."""
    return string % variables if variables else string


def _default_locale() -> str:
    """Fallback locale resolver — plain English when the app doesn't wire one."""
    return "en"


class WikiStore:
    """Wiki persistence + markdown seed/backfill, bound to one DB + uploads dir.

    Parameters are keyword-only so call sites read as configuration,
    not positional plumbing.

    - `db_path` — absolute SQLite path, or a callable returning one.
    - `uploads_dir` — absolute directory for saved images, or a callable.
      Accepting callables lets tests monkey-patch the app's module-level
      `_DB_PATH` / `UPLOADS_DIR` and have every method re-resolve.
    - `locale_resolver` — callable returning `"en" | "es" | "de"` used
      by every read that returns localised text. Default returns `"en"`
      so the library works outside a Flask request context.
    - `gettext` — optional translator for error messages. Identity by
      default; apps with Babel pass `flask_babel.gettext`.
    """

    def __init__(
        self,
        *,
        db_path: "str | Callable[[], str]",
        uploads_dir: "str | Callable[[], str]",
        locale_resolver: Callable[[], str] = _default_locale,
        gettext: Callable[..., str] = _default_gettext,
    ) -> None:
        self._db_path_resolver: Callable[[], str] = (
            db_path if callable(db_path) else (lambda p=db_path: p)
        )
        self._uploads_dir_resolver: Callable[[], str] = (
            uploads_dir if callable(uploads_dir) else (lambda p=uploads_dir: p)
        )
        self._locale = locale_resolver
        self._ = gettext

    # ------------------------------------------------------------------
    # connection + schema
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path_resolver())
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS wiki_pages ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  parent_id INTEGER,"
                "  slug TEXT NOT NULL,"
                "  title TEXT NOT NULL,"
                "  content TEXT NOT NULL DEFAULT '',"
                "  title_es TEXT,"
                "  content_es TEXT,"
                "  title_de TEXT,"
                "  content_de TEXT,"
                "  sort_order INTEGER NOT NULL DEFAULT 0,"
                "  min_role TEXT,"
                "  created_at INTEGER NOT NULL,"
                "  updated_at INTEGER NOT NULL,"
                "  FOREIGN KEY(parent_id) REFERENCES wiki_pages(id) ON DELETE CASCADE,"
                "  UNIQUE(parent_id, slug)"
                ")"
            )
            # Backfill columns added over time (legacy DBs).
            cols = {row[1] for row in conn.execute("PRAGMA table_info(wiki_pages)").fetchall()}
            for col in ("min_role", "title_es", "content_es", "title_de", "content_de"):
                if col not in cols:
                    conn.execute(f"ALTER TABLE wiki_pages ADD COLUMN {col} TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_wiki_parent_sort "
                "ON wiki_pages(parent_id, sort_order)"
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # localisation + row shaping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_get(row: sqlite3.Row, key: str):
        """Safe getter for optional columns that may not exist on older schemas."""
        try:
            return row[key]
        except (IndexError, KeyError):
            return None

    def _localize_title(self, row: sqlite3.Row, locale: str) -> str:
        if locale == "es":
            val = self._row_get(row, "title_es")
            if val:
                return val
        elif locale == "de":
            val = self._row_get(row, "title_de")
            if val:
                return val
        return row["title"]

    def _localize_content(self, row: sqlite3.Row, locale: str) -> str:
        if locale == "es":
            val = self._row_get(row, "content_es")
            if val:
                return val
        elif locale == "de":
            val = self._row_get(row, "content_de")
            if val:
                return val
        return row["content"] or ""

    def _row_to_dict(self, row: sqlite3.Row, locale: Optional[str] = None) -> dict:
        loc = locale or self._locale()
        return {
            "id": row["id"],
            "parent_id": row["parent_id"],
            "slug": row["slug"],
            "title": self._localize_title(row, loc),
            "content": self._localize_content(row, loc),
            "sort_order": row["sort_order"],
            "min_role": row["min_role"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # ------------------------------------------------------------------
    # slug helpers + validation
    # ------------------------------------------------------------------

    @staticmethod
    def _unique_slug(
        conn: sqlite3.Connection,
        parent_id: Optional[int],
        base: str,
        exclude_id: Optional[int] = None,
    ) -> str:
        slug = base
        i = 2
        while True:
            q = "SELECT id FROM wiki_pages WHERE "
            params: list = []
            q += "parent_id IS ? " if parent_id is None else "parent_id = ? "
            params.append(parent_id)
            q += "AND slug = ?"
            params.append(slug)
            if exclude_id is not None:
                q += " AND id != ?"
                params.append(exclude_id)
            row = conn.execute(q, params).fetchone()
            if not row:
                return slug
            slug = f"{base}-{i}"
            i += 1

    def _normalize_min_role(self, value) -> Optional[str]:
        if value is None or value == "":
            return None
        if value not in VALID_MIN_ROLES:
            raise ValueError(self._("invalid min_role: %(value)r", value=value))
        return value

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------

    def list_tree(self, user_role: Optional[str] = None) -> list:
        """Return a nested list of pages as a tree.

        If `user_role` is given, pages (and their subtrees) the role
        cannot see are filtered out. `None` means "show everything"
        (internal/admin callers).
        """
        loc = self._locale()
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, parent_id, slug, title, title_es, title_de, sort_order, "
                "min_role, created_at, updated_at "
                "FROM wiki_pages ORDER BY sort_order ASC, title COLLATE NOCASE ASC"
            ).fetchall()
        finally:
            conn.close()
        by_parent: dict = {}
        for row in rows:
            if user_role is not None and not user_can_see(row["min_role"], user_role):
                continue
            node = {
                "id": row["id"],
                "parent_id": row["parent_id"],
                "slug": row["slug"],
                "title": self._localize_title(row, loc),
                "sort_order": row["sort_order"],
                "min_role": row["min_role"],
                "children": [],
            }
            by_parent.setdefault(row["parent_id"], []).append(node)
        roots = by_parent.get(None, [])

        def attach(nodes):
            for n in nodes:
                n["children"] = by_parent.get(n["id"], [])
                attach(n["children"])

        attach(roots)
        return roots

    def get_page(self, page_id: int) -> Optional[dict]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def get_first_page(self, user_role: Optional[str] = None) -> Optional[dict]:
        """Return the first root page visible to the user (for default landing)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM wiki_pages WHERE parent_id IS NULL "
                "ORDER BY sort_order ASC, title COLLATE NOCASE ASC"
            ).fetchall()
        finally:
            conn.close()
        for row in rows:
            if user_role is None or user_can_see(row["min_role"], user_role):
                return self._row_to_dict(row)
        return None

    def get_breadcrumb(self, page_id: int) -> list:
        """Return list of `{id, title}` from root to page_id (inclusive)."""
        loc = self._locale()
        conn = self._connect()
        try:
            chain: list = []
            cur_id: Optional[int] = page_id
            seen: set = set()
            while cur_id is not None:
                if cur_id in seen:
                    break
                seen.add(cur_id)
                row = conn.execute(
                    "SELECT id, parent_id, title, title_es, title_de "
                    "FROM wiki_pages WHERE id = ?",
                    (cur_id,),
                ).fetchone()
                if not row:
                    break
                chain.append({"id": row["id"], "title": self._localize_title(row, loc)})
                cur_id = row["parent_id"]
            chain.reverse()
            return chain
        finally:
            conn.close()

    def is_empty(self) -> bool:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM wiki_pages").fetchone()
            return (row["c"] or 0) == 0
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # mutations
    # ------------------------------------------------------------------

    def create_page(
        self,
        title: str,
        parent_id: Optional[int] = None,
        content: str = "",
        min_role: Optional[str] = None,
        title_es: Optional[str] = None,
        content_es: Optional[str] = None,
        title_de: Optional[str] = None,
        content_de: Optional[str] = None,
    ) -> dict:
        title = (title or "").strip()
        if not title:
            raise ValueError(self._("title required"))
        min_role = self._normalize_min_role(min_role)
        conn = self._connect()
        try:
            if parent_id is not None:
                parent = conn.execute(
                    "SELECT id FROM wiki_pages WHERE id = ?", (parent_id,)
                ).fetchone()
                if not parent:
                    raise ValueError(self._("parent not found"))
            slug = self._unique_slug(conn, parent_id, slugify(title))
            now = int(time.time())
            max_order_row = conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) AS m FROM wiki_pages WHERE "
                + ("parent_id IS ?" if parent_id is None else "parent_id = ?"),
                (parent_id,),
            ).fetchone()
            next_order = (max_order_row["m"] if max_order_row["m"] is not None else -1) + 1
            cur = conn.execute(
                "INSERT INTO wiki_pages (parent_id, slug, title, content, "
                "title_es, content_es, title_de, content_de, "
                "sort_order, min_role, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (parent_id, slug, title, content,
                 title_es, content_es, title_de, content_de,
                 next_order, min_role, now, now),
            )
            page_id = cur.lastrowid
            conn.commit()
            row = conn.execute("SELECT * FROM wiki_pages WHERE id = ?", (page_id,)).fetchone()
            return self._row_to_dict(row)
        finally:
            conn.close()

    _UNSET = object()

    def update_page(
        self,
        page_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        min_role=_UNSET,
    ) -> dict:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
            ).fetchone()
            if not row:
                raise ValueError(self._("page not found"))
            new_title = row["title"] if title is None else (title or "").strip()
            if not new_title:
                raise ValueError(self._("title required"))
            new_content = row["content"] if content is None else content
            new_slug = row["slug"]
            if title is not None and new_title != row["title"]:
                new_slug = self._unique_slug(
                    conn, row["parent_id"], slugify(new_title), exclude_id=page_id
                )
            new_min_role = (
                row["min_role"] if min_role is self._UNSET
                else self._normalize_min_role(min_role)
            )
            now = int(time.time())
            conn.execute(
                "UPDATE wiki_pages SET title = ?, slug = ?, content = ?, "
                "min_role = ?, updated_at = ? WHERE id = ?",
                (new_title, new_slug, new_content, new_min_role, now, page_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
            ).fetchone()
            return self._row_to_dict(row)
        finally:
            conn.close()

    def delete_page(self, page_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM wiki_pages WHERE id = ?", (page_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def move_page(
        self,
        page_id: int,
        new_parent_id: Optional[int],
        new_sort_order: Optional[int] = None,
    ) -> dict:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
            ).fetchone()
            if not row:
                raise ValueError(self._("page not found"))
            if new_parent_id is not None:
                if new_parent_id == page_id:
                    raise ValueError(self._("cannot parent page to itself"))
                # prevent cycles
                cur_ancestor: Optional[int] = new_parent_id
                while cur_ancestor is not None:
                    anc = conn.execute(
                        "SELECT parent_id FROM wiki_pages WHERE id = ?",
                        (cur_ancestor,),
                    ).fetchone()
                    if not anc:
                        raise ValueError(self._("new parent not found"))
                    if anc["parent_id"] == page_id:
                        raise ValueError(self._("move would create a cycle"))
                    cur_ancestor = anc["parent_id"]
            slug = self._unique_slug(conn, new_parent_id, row["slug"], exclude_id=page_id)
            if new_sort_order is None:
                max_order_row = conn.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) AS m FROM wiki_pages WHERE "
                    + ("parent_id IS ?" if new_parent_id is None else "parent_id = ?"),
                    (new_parent_id,),
                ).fetchone()
                new_sort_order = (
                    (max_order_row["m"] if max_order_row["m"] is not None else -1) + 1
                )
            conn.execute(
                "UPDATE wiki_pages SET parent_id = ?, slug = ?, sort_order = ?, "
                "updated_at = ? WHERE id = ?",
                (new_parent_id, slug, new_sort_order, int(time.time()), page_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM wiki_pages WHERE id = ?", (page_id,)
            ).fetchone()
            return self._row_to_dict(row)
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # seed + backfill
    # ------------------------------------------------------------------

    def seed(self, articles) -> bool:
        """Seed initial content or backfill translations on an existing wiki.

        `articles` is an iterable of dicts with the shape used by each
        app's `wiki_seed_content.ARTICLES` — `{key, parent, title:
        {en, es, de}, content: {en, es, de}, min_role}`. Order matters:
        a child must appear after its parent so `key_to_id` can resolve.

        Returns True if anything was written (first-time seed or a
        backfill that updated at least one row), False otherwise.
        """
        if self.is_empty():
            key_to_id: dict = {}
            for art in articles:
                parent_id = key_to_id.get(art["parent"]) if art["parent"] else None
                page = self.create_page(
                    title=art["title"]["en"],
                    parent_id=parent_id,
                    content=art["content"]["en"],
                    min_role=art["min_role"],
                    title_es=art["title"].get("es"),
                    content_es=art["content"].get("es"),
                    title_de=art["title"].get("de"),
                    content_de=art["content"].get("de"),
                )
                key_to_id[art["key"]] = page["id"]
            return True
        return self._backfill_translations(articles)

    def _backfill_translations(self, articles) -> bool:
        """Fill `title_es` / `content_es` / `title_de` / `content_de` on
        existing rows whose English title matches an article. Idempotent:
        only updates columns that are still NULL.
        """
        conn = self._connect()
        touched = False
        try:
            for art in articles:
                en_title = art["title"]["en"]
                row = conn.execute(
                    "SELECT id, title_es, content_es, title_de, content_de "
                    "FROM wiki_pages WHERE title = ? LIMIT 1",
                    (en_title,),
                ).fetchone()
                if not row:
                    continue
                updates: list = []
                params: list = []
                if not self._row_get(row, "title_es") and art["title"].get("es"):
                    updates.append("title_es = ?")
                    params.append(art["title"]["es"])
                if not self._row_get(row, "content_es") and art["content"].get("es"):
                    updates.append("content_es = ?")
                    params.append(art["content"]["es"])
                if not self._row_get(row, "title_de") and art["title"].get("de"):
                    updates.append("title_de = ?")
                    params.append(art["title"]["de"])
                if not self._row_get(row, "content_de") and art["content"].get("de"):
                    updates.append("content_de = ?")
                    params.append(art["content"]["de"])
                if updates:
                    params.append(row["id"])
                    conn.execute(
                        f"UPDATE wiki_pages SET {', '.join(updates)} WHERE id = ?",
                        params,
                    )
                    touched = True
            if touched:
                conn.commit()
        finally:
            conn.close()
        return touched

    # ------------------------------------------------------------------
    # uploads
    # ------------------------------------------------------------------

    def save_upload(self, file_storage) -> dict:
        """Save uploaded image and return `{'url': str, 'filename': str}`.

        Raises `ValueError` when the file extension is not in the
        allow-list (png/jpg/jpeg/gif/webp/svg).
        """
        filename = file_storage.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in _ALLOWED_IMG_EXTS:
            raise ValueError(self._("extension '%(ext)s' not allowed", ext=ext))
        safe_base = safe_upload_name(
            filename.rsplit(".", 1)[0] if "." in filename else filename
        )
        stamp = int(time.time() * 1000)
        final_name = f"{stamp}-{safe_base}.{ext}"
        uploads_dir = self._uploads_dir_resolver()
        full_path = os.path.join(uploads_dir, final_name)
        file_storage.save(full_path)
        return {"url": f"/api/wiki/uploads/{final_name}", "filename": final_name}

    def upload_path(self, filename: str) -> Optional[str]:
        """Resolve a filename to its absolute path, or None if unsafe/missing.

        Rejects anything that would escape `uploads_dir` via `..` or an
        absolute path, and anything that doesn't exist on disk.
        """
        safe = os.path.basename(filename or "")
        if not safe or safe != filename:
            return None
        full = os.path.join(self._uploads_dir_resolver(), safe)
        if not os.path.isfile(full):
            return None
        return full
