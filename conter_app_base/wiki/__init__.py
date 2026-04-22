"""Wiki chassis — SQLite tree of markdown pages + uploads + rendering.

Every Conter app ships the same in-app wiki: a tree of admin-editable
markdown pages, per-page role gating, ES/DE translations with an
English fallback, image uploads, and a python-markdown renderer. The
actual *content* (which articles to seed, what screenshots exist) is
per-app and stays in the app repo — only the infrastructure is shared.

Canonical usage (see `app/services/wiki_service.py` in conter-stats
for a working example):

    from conter_app_base.wiki import WikiStore, render_markdown, slugify

    _store = WikiStore(
        db_path=lambda: _DB_PATH,           # late binding for tests
        uploads_dir=lambda: UPLOADS_DIR,
        locale_resolver=_current_locale,    # returns "en" | "es" | "de"
        gettext=flask_babel.gettext,        # optional, identity default
    )

    init_wiki_db = _store.init_schema
    list_tree    = _store.list_tree
    get_page     = _store.get_page
    ...

    # App-specific seed — ARTICLES is owned by the app.
    def seed_initial_content():
        from app.services.wiki_seed_content import ARTICLES
        return _store.seed(ARTICLES)
"""
from conter_app_base.wiki.markdown import render_markdown
from conter_app_base.wiki.store import WikiStore
from conter_app_base.wiki.utils import (
    ROLE_RANK,
    VALID_MIN_ROLES,
    safe_upload_name,
    slugify,
    user_can_see,
)

__all__ = [
    "ROLE_RANK",
    "VALID_MIN_ROLES",
    "WikiStore",
    "render_markdown",
    "safe_upload_name",
    "slugify",
    "user_can_see",
]
