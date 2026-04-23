"""Unit tests for `central_server_app_foundation.settings_ui`.

Covers the `SettingsShell` registration API (ordering, role gating)
and the blueprint (injection of `chassis_settings_sections`, role
resolver callbacks, static CSS route).
"""
from __future__ import annotations

import pytest
from flask import Flask, render_template_string

from central_server_app_foundation.settings_ui import (
    SettingsButton,
    SettingsSection,
    SettingsShell,
    create_settings_blueprint,
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

class TestSettingsSection:
    def test_defaults_to_admin_only(self):
        s = SettingsSection(key="x", title="X")
        assert s.admin_only is True
        assert s.supervisor_only is False
        assert s.buttons == []

    def test_admin_only_hides_from_regular_users(self):
        s = SettingsSection(key="x", title="X", admin_only=True)
        assert not s.is_visible(is_admin=False, is_supervisor=False)
        assert s.is_visible(is_admin=True)

    def test_supervisor_only_accepts_admins(self):
        """Admins implicitly pass supervisor-only gates (same convention
        as the sidebar + `can_publish(role)` in conter-stats)."""
        s = SettingsSection(
            key="x", title="X", admin_only=False, supervisor_only=True
        )
        assert not s.is_visible(is_admin=False, is_supervisor=False)
        assert s.is_visible(is_admin=False, is_supervisor=True)
        assert s.is_visible(is_admin=True, is_supervisor=False)

    def test_public_section_visible_to_everyone(self):
        s = SettingsSection(
            key="x", title="X", admin_only=False, supervisor_only=False
        )
        assert s.is_visible(is_admin=False, is_supervisor=False)


class TestSettingsShell:
    def test_section_returns_entry_and_preserves_order(self):
        sh = SettingsShell()
        a = sh.section("a", title="A")
        b = sh.section("b", title="B")
        c = sh.section("c", title="C")
        assert isinstance(a, SettingsSection)
        assert [s.key for s in sh] == ["a", "b", "c"]
        assert [a, b, c] == list(sh)

    def test_len(self):
        sh = SettingsShell()
        assert len(sh) == 0
        sh.section("a", title="A")
        sh.section("b", title="B")
        assert len(sh) == 2

    def test_visible_sections_filters_by_role(self):
        sh = SettingsShell()
        sh.section("public", title="P", admin_only=False)
        sh.section("admin", title="A", admin_only=True)
        sh.section("sup", title="S", admin_only=False, supervisor_only=True)

        as_guest = sh.visible_sections(is_admin=False, is_supervisor=False)
        assert [s.key for s in as_guest] == ["public"]

        as_sup = sh.visible_sections(is_admin=False, is_supervisor=True)
        assert [s.key for s in as_sup] == ["public", "sup"]

        as_admin = sh.visible_sections(is_admin=True)
        assert [s.key for s in as_admin] == ["public", "admin", "sup"]

    def test_section_accepts_buttons(self):
        sh = SettingsShell()
        s = sh.section(
            "cache",
            title="Cache",
            description="Inspect / clear",
            buttons=[
                SettingsButton(label="Stats", onclick="openStats()"),
                SettingsButton(label="Clear", onclick="clearAll()", icon="X"),
            ],
        )
        assert len(s.buttons) == 2
        assert s.buttons[1].icon == "X"


# ---------------------------------------------------------------------------
# Blueprint integration
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_with_shell():
    sh = SettingsShell()
    sh.section(
        "db",
        title="Database",
        description="Connect to MariaDB",
        buttons=[SettingsButton(label="Configure", onclick="openDb()",
                                icon="&#9874;")],
    )
    sh.section(
        "open",
        title="Public Section",
        description="Visible to everyone",
        buttons=[SettingsButton(label="Open", onclick="go()")],
        admin_only=False,
    )
    sh.section(
        "sup",
        title="Supervisor Only",
        admin_only=False,
        supervisor_only=True,
    )

    bp = create_settings_blueprint(shell=sh)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "t"
    app.config["TESTING"] = True
    app.register_blueprint(bp)
    return app, sh


class TestBlueprintContext:
    def test_chassis_settings_sections_injected_for_admin(self, app_with_shell):
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            from flask import session
            session["is_admin"] = True
            ctx = {}
            app.update_template_context(ctx)
        keys = [s.key for s in ctx["chassis_settings_sections"]]
        assert keys == ["db", "open", "sup"]

    def test_chassis_settings_sections_hides_admin_only_for_guests(
        self, app_with_shell
    ):
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        keys = [s.key for s in ctx["chassis_settings_sections"]]
        assert keys == ["open"]

    def test_supervisor_gets_supervisor_only(self, app_with_shell):
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            from flask import session
            session["is_supervisor"] = True
            ctx = {}
            app.update_template_context(ctx)
        keys = [s.key for s in ctx["chassis_settings_sections"]]
        assert "sup" in keys
        assert "db" not in keys

    def test_css_url_exposed(self, app_with_shell):
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        assert ctx["chassis_settings_css_url"].endswith("/settings.css")

    def test_custom_role_resolvers_are_called(self):
        sh = SettingsShell()
        sh.section("db", title="Database", admin_only=True)
        calls = {"admin": 0, "sup": 0}

        def is_admin():
            calls["admin"] += 1
            return True

        def is_sup():
            calls["sup"] += 1
            return False

        bp = create_settings_blueprint(
            shell=sh,
            is_admin_resolver=is_admin,
            is_supervisor_resolver=is_sup,
        )
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        app.register_blueprint(bp)
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        assert calls["admin"] == 1
        assert calls["sup"] == 1
        assert [s.key for s in ctx["chassis_settings_sections"]] == ["db"]

    def test_resolver_exception_treated_as_false(self):
        """A broken role resolver must not 500 the settings page —
        hiding admin-only content on failure is the safe default."""
        sh = SettingsShell()
        sh.section("db", title="Database", admin_only=True)

        def boom():
            raise RuntimeError("bad resolver")

        bp = create_settings_blueprint(shell=sh, is_admin_resolver=boom)
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        app.register_blueprint(bp)
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        assert ctx["chassis_settings_sections"] == []


class TestBlueprintStatic:
    def test_settings_css_is_served(self, app_with_shell):
        app, _sh = app_with_shell
        client = app.test_client()
        resp = client.get("/settings-static/settings.css")
        assert resp.status_code == 200
        assert b".settings-btn" in resp.data
        assert b".settings-buttons" in resp.data


class TestPartialRendering:
    def test_partial_renders_sections_as_cards(self, app_with_shell):
        """Sanity-check the Jinja partial uses the expected class
        names — downstream CSS assumes them."""
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            from flask import session
            session["is_admin"] = True
            html = render_template_string(
                '{% include "central_server_app_foundation/settings/_sections.html" %}'
            )
        assert 'class="card-section' in html
        assert "card-section-last" in html  # last item gets the marker
        assert 'class="section-label"' in html
        assert 'class="settings-buttons"' in html
        assert 'class="settings-btn"' in html
        assert 'data-settings-section="db"' in html
        assert "Database" in html
        assert "openDb()" in html

    def test_partial_hides_admin_only_for_guests(self, app_with_shell):
        app, _sh = app_with_shell
        with app.test_request_context("/"):
            html = render_template_string(
                '{% include "central_server_app_foundation/settings/_sections.html" %}'
            )
        assert "Database" not in html
        assert "Public Section" in html

    def test_partial_supports_href_buttons(self):
        sh = SettingsShell()
        sh.section(
            "link",
            title="External",
            buttons=[SettingsButton(label="Docs", href="/wiki")],
            admin_only=False,
        )
        bp = create_settings_blueprint(shell=sh)
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        app.register_blueprint(bp)
        with app.test_request_context("/"):
            html = render_template_string(
                '{% include "central_server_app_foundation/settings/_sections.html" %}'
            )
        assert '<a class="settings-btn"' in html
        assert 'href="/wiki"' in html
