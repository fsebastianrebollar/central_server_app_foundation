"""Unit tests for `conter_app_base.design`.

Covers the Sidebar API (entry construction, role gating, active-state
resolution) and the blueprint's context processor (what `chassis_*`
variables it exposes and under which conditions).
"""
from __future__ import annotations

import pytest
from flask import Flask

from conter_app_base.design import (
    Sidebar,
    SidebarEntry,
    create_design_blueprint,
)


# ---------------------------------------------------------------------------
# Sidebar API
# ---------------------------------------------------------------------------

class TestSidebarEntry:
    def test_default_active_endpoint_is_own(self):
        e = SidebarEntry(label="Dash", endpoint="main.dash")
        assert e.active_endpoints == frozenset({"main.dash"})

    def test_explicit_active_endpoints_are_used(self):
        e = SidebarEntry(
            label="Reports",
            endpoint="rep.index",
            active_endpoints=frozenset({"rep.index", "rep.daily"}),
        )
        assert "rep.daily" in e.active_endpoints

    def test_hide_for_guests(self):
        e = SidebarEntry(label="X", endpoint="x.y", hide_for_guests=True)
        assert not e.is_visible(is_admin=False, is_guest=True, is_supervisor=False)
        assert e.is_visible(is_admin=False, is_guest=False, is_supervisor=False)

    def test_admin_only(self):
        e = SidebarEntry(label="X", endpoint="x.y", admin_only=True)
        assert not e.is_visible(is_admin=False, is_guest=False, is_supervisor=False)
        assert e.is_visible(is_admin=True, is_guest=False, is_supervisor=False)

    def test_supervisor_only_allows_admins(self):
        """Admins implicitly pass supervisor-only gates — same convention
        as `can_publish(role)` in conter-stats."""
        e = SidebarEntry(label="X", endpoint="x.y", supervisor_only=True)
        assert not e.is_visible(is_admin=False, is_guest=False, is_supervisor=False)
        assert e.is_visible(is_admin=False, is_guest=False, is_supervisor=True)
        assert e.is_visible(is_admin=True, is_guest=False, is_supervisor=False)

    def test_is_active_by_endpoint_match(self):
        e = SidebarEntry(label="X", endpoint="main.x")
        assert e.is_active(endpoint="main.x", request=None)
        assert not e.is_active(endpoint="main.y", request=None)

    def test_is_active_with_custom_callable(self):
        called = {"n": 0}

        def rule(ep, req):
            called["n"] += 1
            return ep.startswith("app.")

        e = SidebarEntry(label="X", endpoint="main.x", active_when=rule)
        assert e.is_active(endpoint="app.anything", request=None)
        assert not e.is_active(endpoint="other.y", request=None)
        assert called["n"] == 2

    def test_active_when_swallows_exceptions(self):
        """Silent-fail is intentional: a broken predicate must not 500 the page."""
        def boom(ep, req):
            raise RuntimeError("bad rule")

        e = SidebarEntry(label="X", endpoint="main.x", active_when=boom)
        assert e.is_active(endpoint="main.x", request=None) is False


class TestSidebar:
    def test_entries_preserve_insertion_order(self):
        sb = Sidebar()
        sb.entry("A", endpoint="a.x")
        sb.entry("B", endpoint="b.x")
        sb.entry("C", endpoint="c.x")
        labels = [e.label for e in sb]
        assert labels == ["A", "B", "C"]

    def test_len(self):
        sb = Sidebar()
        assert len(sb) == 0
        sb.entry("A", endpoint="a.x")
        sb.entry("B", endpoint="b.x")
        assert len(sb) == 2

    def test_entry_returns_the_created_entry(self):
        sb = Sidebar()
        e = sb.entry("A", endpoint="a.x", icon="&#9632;")
        assert isinstance(e, SidebarEntry)
        assert e.icon == "&#9632;"


# ---------------------------------------------------------------------------
# Blueprint integration
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_with_design():
    """Minimal Flask app wired with the design blueprint + fake endpoints.

    Every endpoint the sidebar references must be registered so `url_for`
    resolves; otherwise the context processor silently drops the entry.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "t"
    app.config["TESTING"] = True

    # Stub endpoints the design blueprint + sidebar will resolve.
    @app.route("/login")
    def _login():
        return "login"

    @app.route("/logout", methods=["POST", "GET"])
    def _logout():
        return "logout"

    @app.route("/user")
    def _user():
        return "user"

    @app.route("/lang/<lang>")
    def _lang(lang):
        return lang

    @app.route("/")
    def _home():
        return "home"

    @app.route("/dash")
    def _dash():
        return "dash"

    @app.route("/admin-only")
    def _admin():
        return "admin"

    sb = Sidebar()
    sb.entry("Home", endpoint="_home", icon="H")
    sb.entry("Dash", endpoint="_dash", icon="D", hide_for_guests=True)
    sb.entry("Admin", endpoint="_admin", icon="A", admin_only=True)

    bp = create_design_blueprint(
        sidebar=sb,
        brand_short="TT",
        brand_full="Test App",
        brand_endpoint="_home",
        user_profile_endpoint="_user",
        logout_endpoint="_logout",
        language_switch_endpoint="_lang",
        supported_languages=("en", "es"),
        theme_save_url="/api/theme",
    )
    app.register_blueprint(bp)
    return app


class TestBlueprintContext:
    def test_chassis_brand_exposed(self, app_with_design):
        with app_with_design.test_request_context("/"):
            ctx = {}
            app_with_design.update_template_context(ctx)
        brand = ctx["chassis_brand"]
        assert brand["short"] == "TT"
        assert brand["full"] == "Test App"
        assert brand["url"] == "/"

    def test_chassis_endpoints_resolved(self, app_with_design):
        with app_with_design.test_request_context("/"):
            ctx = {}
            app_with_design.update_template_context(ctx)
        ep = ctx["chassis_endpoints"]
        assert ep["user_profile"] == "/user"
        assert ep["logout"] == "/logout"
        assert ep["theme_save"] == "/api/theme"
        assert ep["lang"]["en"] == "/lang/en"
        assert ep["lang"]["es"] == "/lang/es"

    def test_guest_hides_dashboard(self, app_with_design):
        client = app_with_design.test_client()
        with client.session_transaction() as s:
            s["is_guest"] = True
        with app_with_design.test_request_context("/"):
            from flask import session
            session["is_guest"] = True
            ctx = {}
            app_with_design.update_template_context(ctx)
        labels = [i["entry"].label for i in ctx["chassis_sidebar"]]
        assert "Dash" not in labels
        assert "Home" in labels

    def test_admin_only_requires_admin(self, app_with_design):
        with app_with_design.test_request_context("/"):
            ctx = {}
            app_with_design.update_template_context(ctx)
        # Unauthenticated: no session flags → Admin entry is hidden.
        assert "Admin" not in [i["entry"].label for i in ctx["chassis_sidebar"]]

        with app_with_design.test_request_context("/"):
            from flask import session
            session["is_admin"] = True
            ctx = {}
            app_with_design.update_template_context(ctx)
        assert "Admin" in [i["entry"].label for i in ctx["chassis_sidebar"]]

    def test_is_active_endpoint_matches(self, app_with_design):
        with app_with_design.test_request_context("/"):
            ctx = {}
            app_with_design.update_template_context(ctx)
        # On "/" the request endpoint is `_home` → Home is active, rest aren't.
        by_label = {i["entry"].label: i["is_active"] for i in ctx["chassis_sidebar"]}
        assert by_label["Home"] is True

    def test_bad_endpoint_is_silently_dropped(self, app_with_design):
        """If an app references a nonexistent endpoint, the entry vanishes
        instead of 500-ing the whole page. Defensive, matches wiki/auth."""
        sb = Sidebar()
        sb.entry("Ghost", endpoint="nope.nowhere")
        sb.entry("Real", endpoint="_home")
        bp = create_design_blueprint(
            sidebar=sb,
            brand_short="X",
            brand_full="X",
            brand_endpoint="_home",
        )
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        app.config["TESTING"] = True

        @app.route("/")
        def _home():
            return "h"

        app.register_blueprint(bp)
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        labels = [i["entry"].label for i in ctx["chassis_sidebar"]]
        assert labels == ["Real"]

    def test_supervisor_resolver_called(self, app_with_design):
        """The callable gets invoked exactly when role is evaluated."""
        calls = {"n": 0}

        def resolver():
            calls["n"] += 1
            return True

        sb = Sidebar()
        sb.entry("Sup", endpoint="_home", supervisor_only=True)
        bp = create_design_blueprint(
            sidebar=sb,
            brand_short="X",
            brand_full="X",
            brand_endpoint="_home",
            is_supervisor_resolver=resolver,
        )
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "t"
        app.config["TESTING"] = True

        @app.route("/")
        def _home():
            return "h"

        app.register_blueprint(bp)
        with app.test_request_context("/"):
            ctx = {}
            app.update_template_context(ctx)
        assert calls["n"] == 1
        assert [i["entry"].label for i in ctx["chassis_sidebar"]] == ["Sup"]


class TestBlueprintStatic:
    def test_chassis_js_is_served(self, app_with_design):
        client = app_with_design.test_client()
        resp = client.get("/design-static/chassis.js")
        assert resp.status_code == 200
        assert b"theme" in resp.data.lower()
        assert b"sidebar" in resp.data.lower()
