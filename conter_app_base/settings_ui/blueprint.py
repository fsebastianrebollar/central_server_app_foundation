"""Flask blueprint exposing the settings shell.

The blueprint's job is narrow on purpose:

- Serve `settings.css` (the section grid + button styles moved out of
  each app's CSS so they can share the same look).
- Inject `chassis_settings_sections` as a context variable on every
  request so `{% include "conter_app_base/settings/_sections.html" %}`
  Just Works regardless of which view renders.
- Resolve admin / supervisor roles through app-provided callables. If no
  resolvers are passed the blueprint falls back to `session["is_admin"]`
  / `session["is_supervisor"]`, which matches every Conter app so far.

The `/settings` *route* is NOT owned by the chassis. Apps already have a
tangle of per-domain context they need to pass to the template (column
configs, DB config, report schedules, etc.), so making the chassis own
the view would either leak those concerns into the library or force an
awkward callback soup. The shell is enough — it renders the nav; the
app owns the page.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flask import Blueprint, session

from .sections import SettingsShell

_DEFAULT_URL_PREFIX = "/settings-static"


def _default_is_admin() -> bool:
    return bool(session.get("is_admin"))


def _default_is_supervisor() -> bool:
    return bool(session.get("is_supervisor"))


def create_settings_blueprint(
    *,
    shell: SettingsShell,
    url_prefix: str = _DEFAULT_URL_PREFIX,
    is_admin_resolver: Callable[[], bool] | None = None,
    is_supervisor_resolver: Callable[[], bool] | None = None,
) -> Blueprint:
    """Build the settings-shell blueprint.

    Parameters
    ----------
    shell
        The populated `SettingsShell`. Sections are filtered per-request
        based on the resolved role booleans, so the same shell instance
        can back both admin and non-admin views.
    url_prefix
        Where `settings.css` is served from. Defaults to `/settings-static`
        so it can't collide with either `/static` (the app) or
        `/design-static` (the design blueprint).
    is_admin_resolver / is_supervisor_resolver
        Optional callables that report the current user's role. Defaults
        read the standard session flags set by the auth blueprint.
    """
    here = Path(__file__).parent

    bp = Blueprint(
        "settings_ui",
        __name__,
        url_prefix=url_prefix,
        template_folder=str(here / "templates"),
        static_folder=str(here / "static"),
        static_url_path="",
    )

    resolve_admin = is_admin_resolver or _default_is_admin
    resolve_supervisor = is_supervisor_resolver or _default_is_supervisor

    @bp.app_context_processor
    def _inject_sections():
        try:
            is_admin = bool(resolve_admin())
        except Exception:
            is_admin = False
        try:
            is_supervisor = bool(resolve_supervisor())
        except Exception:
            is_supervisor = False

        return {
            "chassis_settings_sections": shell.visible_sections(
                is_admin=is_admin, is_supervisor=is_supervisor
            ),
            "chassis_settings_css_url": f"{url_prefix}/settings.css",
        }

    return bp
