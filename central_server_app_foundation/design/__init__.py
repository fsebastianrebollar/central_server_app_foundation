"""Design chassis — shared base template, sidebar API and chassis JS.

Every Conter app wears the same skeleton: a top header with brand
+ theme/lang controls, a left sidebar with role-gated tabs, flash
toast, an auto-wired cell-value modal, and a small JS runtime for
theme + sidebar toggles.

Only the *domain widgets* (product filter, workspace picker, …)
and the *set of tabs* change between apps. This package ships the
skeleton; apps plug in their tabs via `Sidebar.entry(...)` and their
widgets via Jinja blocks in the base template.

Canonical wiring (see conter-stats's `app/__init__.py` for a working
example):

    from central_server_app_foundation.design import Sidebar, create_design_blueprint

    sidebar = Sidebar()
    sidebar.entry("Dashboard", endpoint="main.dashboard",
                  icon="&#9632;", hide_for_guests=True)
    sidebar.entry("Search",    endpoint="main.index", icon="&#8981;")
    sidebar.entry("Settings",  endpoint="main.settings",
                  icon="&#9881;", admin_only=True)

    app.register_blueprint(create_design_blueprint(
        sidebar=sidebar,
        brand_short="CS",
        brand_full="Conter Stats",
        brand_endpoint="main.dashboard",
    ))

    # In the app's base.html:
    #   {% extends "central_server_app_foundation/design/base.html" %}
    #   {% block header_extra_widgets %} ... {% endblock %}
    #   {% block content %} ... {% endblock %}
"""
from central_server_app_foundation.design.blueprint import create_design_blueprint
from central_server_app_foundation.design.icons import ChassisIcons
from central_server_app_foundation.design.sidebar import Sidebar, SidebarEntry

__all__ = [
    "ChassisIcons",
    "Sidebar",
    "SidebarEntry",
    "create_design_blueprint",
]
