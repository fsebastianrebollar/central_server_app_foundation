"""Dataclasses describing the contents of the `/settings` page.

A `SettingsShell` is an ordered collection of `SettingsSection`s. Each
section has a title, a short description and one or more `SettingsButton`s
that open the section's modal (modals themselves live in the app template
— the shell only renders the clickable entry points).

Role gating mirrors the Sidebar API: `admin_only` and `supervisor_only`
are independent flags; admins implicitly pass supervisor-only gates. The
blueprint's context processor resolves the three role booleans from the
app and hands the filtered list to the template, so the partial only
receives sections the current user is allowed to see.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SettingsButton:
    label: str
    onclick: str = ""
    icon: str = ""
    href: str | None = None
    extra_class: str = ""


@dataclass
class SettingsSection:
    key: str
    title: str
    description: str = ""
    buttons: list[SettingsButton] = field(default_factory=list)
    admin_only: bool = True
    supervisor_only: bool = False
    extra_class: str = ""

    def is_visible(
        self, *, is_admin: bool, is_supervisor: bool = False
    ) -> bool:
        if self.admin_only and not is_admin:
            return False
        if self.supervisor_only and not (is_supervisor or is_admin):
            return False
        return True


class SettingsShell:
    """Ordered registry of `SettingsSection`s.

    Entries preserve insertion order so the rendered page layout is
    stable and predictable. Apps may register sections at import time
    (e.g. in a module called from `create_app()`) and pass the shell
    to `create_settings_blueprint()`.
    """

    def __init__(self) -> None:
        self._sections: list[SettingsSection] = []

    def section(
        self,
        key: str,
        *,
        title: str,
        description: str = "",
        buttons: list[SettingsButton] | None = None,
        admin_only: bool = True,
        supervisor_only: bool = False,
        extra_class: str = "",
    ) -> SettingsSection:
        s = SettingsSection(
            key=key,
            title=title,
            description=description,
            buttons=list(buttons or []),
            admin_only=admin_only,
            supervisor_only=supervisor_only,
            extra_class=extra_class,
        )
        self._sections.append(s)
        return s

    def visible_sections(
        self, *, is_admin: bool, is_supervisor: bool = False
    ) -> list[SettingsSection]:
        return [
            s
            for s in self._sections
            if s.is_visible(is_admin=is_admin, is_supervisor=is_supervisor)
        ]

    def __iter__(self):
        return iter(self._sections)

    def __len__(self) -> int:
        return len(self._sections)
