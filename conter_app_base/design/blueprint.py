"""Design blueprint — binds the chassis template + static assets.

Registers:

- `/<design_url_prefix>/chassis.js` — theme + sidebar runtime
  (served via Flask's blueprint `static_folder` — no custom route).
- A context processor injecting `sidebar_rendered` (a list of
  `(entry, url, is_active)` tuples), the brand tuple, and the
  endpoints the chassis template needs (`url_for`-resolved theme
  save, language switch, user profile, logout).

The blueprint deliberately does **not** serve CSS. Apps keep their
own `style.css` for zero visual regression; a future sub-phase can
cherry-pick the chassis-only rules into the library. Only JS that
is 100% generic (theme toggle, sidebar drawer, ESC handler) ships
here today.
"""
from __future__ import annotations

from typing import Callable

from flask import Blueprint, request, session

from conter_app_base.design.sidebar import Sidebar, SidebarEntry


def create_design_blueprint(
    *,
    sidebar: Sidebar,
    brand_short: str,
    brand_full: str,
    brand_endpoint: str,
    user_profile_endpoint: str | None = None,
    logout_endpoint: str | None = None,
    language_switch_endpoint: str | None = None,
    supported_languages: list[str] | tuple[str, ...] = ("en", "es", "de"),
    theme_save_url: str = "/api/theme",
    is_supervisor_resolver: Callable[[], bool] | None = None,
    url_prefix: str = "/design",
) -> Blueprint:
    """Build the design blueprint.

    The blueprint holds the shared `templates/` + `static/` folders
    so `{% extends "conter_app_base/design/base.html" %}` and
    `url_for('design.static', filename='chassis.js')` both work in
    app templates without any extra wiring.

    `is_supervisor_resolver` lets apps report role beyond `is_admin`
    (conter-stats has an explicit "supervisor" role stored in the
    user row). Default: no one is a supervisor — fine for apps with
    just admin/user roles.
    """
    bp = Blueprint(
        "design",
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path=url_prefix + "-static",
    )

    def _resolve_supervisor() -> bool:
        if is_supervisor_resolver is None:
            return False
        try:
            return bool(is_supervisor_resolver())
        except Exception:
            return False

    @bp.app_context_processor
    def _inject_chassis_context():
        # Lazy import — running under app context, so safe.
        from flask import url_for

        is_admin = bool(session.get("is_admin"))
        is_guest = bool(session.get("is_guest"))
        is_supervisor = _resolve_supervisor()
        endpoint = request.endpoint if request else None

        rendered: list[dict] = []
        for e in sidebar:
            if not e.is_visible(
                is_admin=is_admin,
                is_guest=is_guest,
                is_supervisor=is_supervisor,
            ):
                continue
            try:
                url = url_for(e.endpoint)
            except Exception:
                continue
            rendered.append({
                "entry": e,
                "url": url,
                "is_active": e.is_active(
                    endpoint=endpoint, request=request
                ),
            })

        try:
            brand_url = url_for(brand_endpoint)
        except Exception:
            brand_url = "/"

        profile_url = None
        if user_profile_endpoint:
            try:
                profile_url = url_for(user_profile_endpoint)
            except Exception:
                profile_url = None

        logout_url = None
        if logout_endpoint:
            try:
                logout_url = url_for(logout_endpoint)
            except Exception:
                logout_url = None

        lang_urls: dict[str, str] = {}
        if language_switch_endpoint:
            for lang in supported_languages:
                try:
                    lang_urls[lang] = url_for(
                        language_switch_endpoint, lang=lang
                    )
                except Exception:
                    pass

        return {
            "chassis_sidebar": rendered,
            "chassis_brand": {
                "short": brand_short,
                "full": brand_full,
                "url": brand_url,
            },
            "chassis_endpoints": {
                "user_profile": profile_url,
                "logout": logout_url,
                "lang": lang_urls,
                "theme_save": theme_save_url,
            },
            "chassis_supported_languages": list(supported_languages),
        }

    return bp


__all__ = ["create_design_blueprint"]
