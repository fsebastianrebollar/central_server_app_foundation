"""Shared `/settings` shell for Conter apps.

Each app owns its domain-specific sections (DB connection, column configs,
report schedules, whatever). The library owns the *pattern*: section grid
layout, button cluster styling, role gating, and the Jinja partial that
renders it. Apps register sections via `SettingsShell.section(...)` and
drop `{% include "conter_app_base/settings/_sections.html" %}` where
they want the list rendered. Modals, JS and backing endpoints stay
per-app — the chassis deliberately does not try to own those.
"""
from __future__ import annotations

from .sections import SettingsButton, SettingsSection, SettingsShell
from .blueprint import create_settings_blueprint

__all__ = [
    "SettingsButton",
    "SettingsSection",
    "SettingsShell",
    "create_settings_blueprint",
]
