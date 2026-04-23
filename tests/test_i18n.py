"""Unit + integration tests for `central_server_app_foundation.i18n`."""
from __future__ import annotations

import os

import pytest
from flask import Flask
from flask_babel import gettext

from central_server_app_foundation.i18n import (
    DEFAULT_SUPPORTED_LANGUAGES,
    init_babel,
    make_locale_resolver,
)


# ---------------------------------------------------------------------------
# Locale resolver
# ---------------------------------------------------------------------------

class TestLocaleResolver:
    def test_returns_default_outside_request_context(self):
        r = make_locale_resolver(default_language="en")
        assert r() == "en"

    def test_returns_default_when_no_signal(self):
        r = make_locale_resolver()
        app = Flask(__name__)
        with app.test_request_context("/"):
            assert r() == "en"

    def test_session_key_wins_when_supported(self):
        r = make_locale_resolver(supported_languages=("en", "es"))
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        with app.test_request_context("/"):
            from flask import session
            session["lang"] = "es"
            assert r() == "es"

    def test_cookie_is_used_when_session_missing(self):
        r = make_locale_resolver(supported_languages=("en", "de"))
        app = Flask(__name__)
        with app.test_request_context("/", headers={"Cookie": "lang=de"}):
            assert r() == "de"

    def test_accept_language_fallback(self):
        r = make_locale_resolver(supported_languages=("en", "es", "de"))
        app = Flask(__name__)
        with app.test_request_context(
            "/", headers={"Accept-Language": "de-DE,de;q=0.9"}
        ):
            assert r() == "de"

    def test_unsupported_session_ignored(self):
        r = make_locale_resolver(
            supported_languages=("en", "es"), default_language="en"
        )
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        with app.test_request_context("/"):
            from flask import session
            session["lang"] = "zz"
            assert r() == "en"


# ---------------------------------------------------------------------------
# init_babel wiring
# ---------------------------------------------------------------------------

class TestInitBabel:
    def test_sets_default_locale(self):
        app = Flask(__name__)
        init_babel(app, default_language="es")
        assert app.config["BABEL_DEFAULT_LOCALE"] == "es"

    def test_library_dir_prepended_to_translation_path(self):
        app = Flask(__name__)
        init_babel(app, translation_dirs=("app_translations",))
        dirs = app.config["BABEL_TRANSLATION_DIRECTORIES"].split(";")
        assert len(dirs) == 2
        assert dirs[0].endswith(os.path.join("i18n", "translations"))
        assert dirs[1] == "app_translations"

    def test_only_library_dir_when_no_app_dirs(self):
        app = Flask(__name__)
        init_babel(app)
        dirs = app.config["BABEL_TRANSLATION_DIRECTORIES"].split(";")
        assert len(dirs) == 1
        assert dirs[0].endswith(os.path.join("i18n", "translations"))

    def test_library_catalog_translates_chassis_string(self):
        """A string that only exists in the library catalog (not the
        app's) must still resolve — proves the bundled .mo loads."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        init_babel(app, supported_languages=("en", "es"))
        with app.test_request_context("/"):
            from flask import session
            session["lang"] = "es"
            # "User Profile" is a library string shipped in auth_ui;
            # it is translated to Spanish in the bundled catalog.
            assert gettext("User Profile") == "Perfil de usuario"

    def test_missing_translation_falls_back_to_source(self):
        """Untranslated keys must return the English source unchanged."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        init_babel(app, supported_languages=("en", "es"))
        with app.test_request_context("/"):
            from flask import session
            session["lang"] = "es"
            assert gettext("zzz-not-a-real-string") == "zzz-not-a-real-string"


class TestDefaults:
    def test_default_languages_are_en_es_de(self):
        assert DEFAULT_SUPPORTED_LANGUAGES == ("en", "es", "de")
