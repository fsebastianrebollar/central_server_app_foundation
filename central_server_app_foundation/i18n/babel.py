"""Babel init helpers.

The library's own translation catalogs live in
`central_server_app_foundation/i18n/translations/`. `init_babel` prepends that path to
whatever the app supplies, so Flask-Babel searches the app catalogs
first and falls back to the library ones when a string isn't translated
at the app level. That means every consumer gets the chassis / auth UI
/ settings UI translations for free — they only need to translate their
domain strings.
"""
from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Any

from flask import has_request_context, request, session
from flask_babel import Babel


DEFAULT_SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "es", "de")


def _library_translations_dir() -> str:
    """Absolute path to the bundled library catalogs."""
    return os.path.join(os.path.dirname(__file__), "translations")


def make_locale_resolver(
    supported_languages: Sequence[str] = DEFAULT_SUPPORTED_LANGUAGES,
    default_language: str = "en",
    session_key: str = "lang",
    cookie_key: str = "lang",
) -> Callable[[], str]:
    """Return a `locale_selector` safe to pass to Flask-Babel.

    Resolution order: session → cookie → `Accept-Language` → default.
    The resolver falls back to `default_language` when called outside a
    request context (tests, background jobs, module-level code),
    matching the pre-extraction conter-stats behaviour so service-layer
    code can wrap error messages with `gettext()` without guarding.
    """
    langs = tuple(supported_languages)

    def _resolver() -> str:
        if not has_request_context():
            return default_language
        session_lang = session.get(session_key, "") if session else ""
        cookie_lang = request.cookies.get(cookie_key, "") if request else ""
        for candidate in (session_lang, cookie_lang):
            if candidate in langs:
                return candidate
        return request.accept_languages.best_match(
            list(langs), default=default_language,
        )

    return _resolver


def init_babel(
    app: Any,
    *,
    supported_languages: Sequence[str] = DEFAULT_SUPPORTED_LANGUAGES,
    default_language: str = "en",
    translation_dirs: Sequence[str] = (),
    locale_selector: Callable[[], str] | None = None,
) -> Babel:
    """Configure Flask-Babel on `app` with merged library+app catalogs.

    `translation_dirs` is a sequence of directory paths (relative to
    `app.root_path` if not absolute). The library's own translation
    directory is prepended so `gettext()` finds app translations first
    and falls back to chassis translations.
    """
    lib_dir = _library_translations_dir()
    dirs = [lib_dir, *translation_dirs] if translation_dirs else [lib_dir]

    app.config["BABEL_DEFAULT_LOCALE"] = default_language
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = ";".join(dirs)

    selector = locale_selector or make_locale_resolver(
        supported_languages=supported_languages,
        default_language=default_language,
    )
    return Babel(app, locale_selector=selector)
