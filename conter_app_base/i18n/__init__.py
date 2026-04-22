"""Shared i18n wiring for Conter apps.

`init_babel(app, supported_languages=...)` sets up Flask-Babel with a
merged translation path that includes both the library's own catalogs
(shipped with `conter_app_base.i18n.translations`) and whatever
additional directory the app points to via `translation_dirs=`.

The library's catalogs translate strings that appear in library-owned
templates (auth_ui / settings_ui / design chassis). Apps then translate
only their own strings on top; any key the app doesn't have falls
through to the library translation, and untranslated keys fall through
to the English source. This is the standard gettext lookup, Flask-Babel
just needs the paths.

`make_locale_resolver(...)` returns a function Flask-Babel can pass to
`Babel(..., locale_selector=...)`. It honours session → cookie →
Accept-Language → default in that order and is safe to call outside
a request context (returns the default).
"""
from __future__ import annotations

from .babel import (
    DEFAULT_SUPPORTED_LANGUAGES,
    init_babel,
    make_locale_resolver,
)

__all__ = [
    "DEFAULT_SUPPORTED_LANGUAGES",
    "init_babel",
    "make_locale_resolver",
]
