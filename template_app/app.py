"""Template App — Flask application factory.

Wires every central_server_app_foundation module so this file serves as
a copy-paste starting point for new Conter apps.

Run:
    python -m template_app.run
    python -m template_app.run --port 5001 --data-dir /tmp/template_data
"""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

from flask import Flask, session

from central_server_app_foundation.auth import UserStore
from central_server_app_foundation.auth_ui import create_auth_blueprint
from central_server_app_foundation.contract import (
    create_health_blueprint,
    override_path,
)
from central_server_app_foundation.design import ChassisIcons, Sidebar, create_design_blueprint
from central_server_app_foundation.i18n import init_babel, make_locale_resolver
from central_server_app_foundation.settings import SettingsStore
from central_server_app_foundation.settings_ui import (
    SettingsButton,
    SettingsShell,
    create_settings_blueprint,
)
from central_server_app_foundation.version import (
    get_uptime_seconds,
    resolve_build_date,
    resolve_version,
)

# ── App identity (each app owns these constants) ─────────────────────────────

APP_NAME = "template-app"
APP_DISPLAY_NAME = "Template App"
APP_DESCRIPTION = "Reference integration of central_server_app_foundation."
CONTRACT_VERSION = "1.3"

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"
_START = time.time()

# ── Data directory ───────────────────────────────────────────────────────────


def _data_dir() -> Path:
    """Returns the active data directory, honouring --data-dir / CONTER_DATA_DIR."""
    base_str = override_path("template_app")
    base = Path(base_str) if base_str else Path(__file__).parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


# ── Module-level store singletons (late-binding db_path) ─────────────────────
# Using lambdas ensures the path is re-evaluated on each DB access so that
# monkeypatching _data_dir in tests works without re-creating the stores.

_user_store = UserStore(
    db_path=lambda: str(_data_dir() / "auth.db"),
    admin_user=os.environ.get("TEMPLATE_ADMIN_USER", "admin"),
    admin_pass=os.environ.get("TEMPLATE_ADMIN_PASS", "changeme"),
)

_settings_store = SettingsStore(
    db_path=lambda: str(_data_dir() / "settings.db"),
)


def _db_probe() -> str:
    """Fresh SQLite probe for /health — never uses the module-level connection."""
    try:
        conn = sqlite3.connect(str(_data_dir() / "auth.db"), timeout=2)
        conn.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
        return "ok"
    except Exception:
        return "error"


# ── Sidebar ───────────────────────────────────────────────────────────────────
# Icons are rendered with |safe so HTML entities work directly.

_sidebar = Sidebar()
_sidebar.entry("Template", endpoint="template.template_page", icon=ChassisIcons.DASHBOARD)
_sidebar.entry("Settings", endpoint="template.settings", icon=ChassisIcons.SETTINGS, admin_only=True)

# ── Settings UI shell ─────────────────────────────────────────────────────────

_settings_shell = SettingsShell()
_settings_shell.section(
    "appearance",
    title="Appearance",
    description="Theme and language preferences are saved automatically when you switch them.",
    buttons=[SettingsButton(label="User profile", icon="&#9881;", href="/user")],
    admin_only=False,
)
_settings_shell.section(
    "welcome",
    title="Welcome Message",
    description="The message shown at the top of the Template page.",
    buttons=[SettingsButton(label="Edit", icon="&#9998;", onclick="openWelcomeModal()")],
    admin_only=True,
)
_settings_shell.section(
    "example",
    title="Example Configuration",
    description="Placeholder section. Replace this with your own domain-specific settings and modal.",
    buttons=[SettingsButton(label="Configure", icon="&#9881;", onclick="openExampleModal()")],
    admin_only=True,
)


# ── Application factory ───────────────────────────────────────────────────────


def create_app(*, start_time: float | None = None) -> Flask:
    """Build and return the configured Flask application.

    `start_time` is captured by run.py before any import so uptime is
    correct across hot reloads. Defaults to module-import time.
    """
    _st = start_time or _START

    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # ── i18n ─────────────────────────────────────────────────────────────────
    # make_locale_resolver resolves: session["lang"] → cookie → Accept-Language → default
    get_locale = make_locale_resolver(
        supported_languages=("en", "es", "de"),
        default_language="en",
    )
    init_babel(app, supported_languages=("en", "es", "de"), locale_selector=get_locale)

    # ── Init schemas (idempotent) ─────────────────────────────────────────────
    _user_store.init_schema()
    _settings_store.init_schema()

    # ── Session context processor ─────────────────────────────────────────────
    # The chassis base.html expects current_user, is_admin, is_guest,
    # current_lang and user_theme as template variables. No chassis module
    # injects these — the app must do it.
    @app.context_processor
    def _inject_session_context():
        return {
            "current_user": session.get("user_id"),
            "is_admin": bool(session.get("is_admin")),
            "is_guest": bool(session.get("is_guest")),
            "current_lang": session.get("lang", "en"),
            "user_theme": session.get("theme", ""),
        }

    # ── Auth ──────────────────────────────────────────────────────────────────
    def _get_pref(username: str, key: str, default: str = "") -> str:
        return _settings_store.get_user_pref(username, key, default)

    def _set_pref(username: str, key: str, value: str) -> None:
        _settings_store.set_user_pref(username, key, value)

    auth_bp = create_auth_blueprint(
        user_store=_user_store,
        post_login_endpoint="template.index",
        supported_languages=("en", "es", "de"),
        allow_guest=True,
        get_user_pref=_get_pref,
        set_user_pref=_set_pref,
        login_brand_short="TA",
        login_brand_full="Template App",
        protected_user="admin",
    )
    app.register_blueprint(auth_bp)

    # ── Design ────────────────────────────────────────────────────────────────
    design_bp = create_design_blueprint(
        sidebar=_sidebar,
        brand_short="TA",
        brand_full="Template App",
        brand_endpoint="template.index",
        user_profile_endpoint="auth.user_profile",
        logout_endpoint="auth.logout",
        language_switch_endpoint="auth.set_language",
        supported_languages=("en", "es", "de"),
        theme_save_url="/api/theme",
    )
    app.register_blueprint(design_bp)

    # ── Settings UI ───────────────────────────────────────────────────────────
    settings_bp = create_settings_blueprint(shell=_settings_shell)
    app.register_blueprint(settings_bp)

    # ── Supervisor contract ───────────────────────────────────────────────────
    health_bp = create_health_blueprint(
        app_name=APP_NAME,
        app_display_name=APP_DISPLAY_NAME,
        app_description=APP_DESCRIPTION,
        contract_version=CONTRACT_VERSION,
        get_version=lambda: resolve_version(_PYPROJECT),
        get_build_date=resolve_build_date,
        get_uptime_seconds=lambda: get_uptime_seconds(_st),
        db_probe=_db_probe,
        icon_path=Path(__file__).parent / "static" / "icon.png",
    )
    app.register_blueprint(health_bp)

    # ── Domain blueprint ──────────────────────────────────────────────────────
    from template_app.routes import create_template_blueprint

    template_bp = create_template_blueprint(settings_store=_settings_store)
    app.register_blueprint(template_bp)

    return app
