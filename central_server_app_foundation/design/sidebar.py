"""Sidebar API — apps declare their nav tabs instead of templating them.

Each app builds a `Sidebar` once at startup and passes it to the
design blueprint factory. The blueprint exposes it on the Jinja
context as `sidebar_entries` (filtered by current role + endpoint
highlighting), which `_sidebar.html` iterates.

An *entry* knows:

- `label` — the visible text (already translated; see `gettext_fn`
  below for translation timing).
- `endpoint` — Flask endpoint name (`"main.dashboard"`), resolved
  with `url_for` at render time so `APPLICATION_ROOT` prefixes are
  applied automatically.
- `icon` — an HTML entity / SVG / text node rendered inside the
  link's icon slot. No constraint on content — it's inserted as
  `|safe`.
- `admin_only` / `hide_for_guests` / `supervisor_only` — visibility
  gates. The blueprint evaluates them against the current session.
- `active_endpoints` — set of endpoint names that should highlight
  this entry. Defaults to `{endpoint}`. Apps pass extra ones for
  "same tab, different pages" (e.g. reports has three endpoints).
- `active_when` — optional callable `(endpoint, request) -> bool`
  for cases the endpoint set can't express (conter-stats has one:
  the test-steps page belongs to Dashboard *or* Search depending
  on how the user got there).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass
class SidebarEntry:
    label: str
    endpoint: str
    icon: str = ""
    admin_only: bool = False
    supervisor_only: bool = False
    hide_for_guests: bool = False
    active_endpoints: frozenset[str] = field(default_factory=frozenset)
    active_when: Callable[[str, object], bool] | None = None

    def __post_init__(self) -> None:
        # Default active set is the entry's own endpoint — saves the
        # app from repeating `active_endpoints={"main.x"}` on every
        # call when the rule is the obvious one.
        if not self.active_endpoints:
            object.__setattr__(
                self, "active_endpoints", frozenset({self.endpoint})
            )
        elif not isinstance(self.active_endpoints, frozenset):
            object.__setattr__(
                self,
                "active_endpoints",
                frozenset(self.active_endpoints),
            )

    def is_visible(
        self, *, is_admin: bool, is_guest: bool, is_supervisor: bool
    ) -> bool:
        if self.hide_for_guests and is_guest:
            return False
        if self.admin_only and not is_admin:
            return False
        if self.supervisor_only and not (is_supervisor or is_admin):
            return False
        return True

    def is_active(self, *, endpoint: str | None, request: object) -> bool:
        if self.active_when is not None:
            try:
                return bool(self.active_when(endpoint or "", request))
            except Exception:
                return False
        return (endpoint or "") in self.active_endpoints


class Sidebar:
    """Ordered collection of `SidebarEntry` rows.

    Entries render in insertion order. The class is intentionally
    a thin shell — the real work (role filtering, active-state
    computation) happens per render in the blueprint's context
    processor, because `session` and `request` are request-scoped.
    """

    def __init__(self) -> None:
        self._entries: list[SidebarEntry] = []

    def entry(
        self,
        label: str,
        *,
        endpoint: str,
        icon: str = "",
        admin_only: bool = False,
        supervisor_only: bool = False,
        hide_for_guests: bool = False,
        active_endpoints: Iterable[str] | None = None,
        active_when: Callable[[str, object], bool] | None = None,
    ) -> SidebarEntry:
        e = SidebarEntry(
            label=label,
            endpoint=endpoint,
            icon=icon,
            admin_only=admin_only,
            supervisor_only=supervisor_only,
            hide_for_guests=hide_for_guests,
            active_endpoints=(
                frozenset(active_endpoints)
                if active_endpoints is not None
                else frozenset()
            ),
            active_when=active_when,
        )
        self._entries.append(e)
        return e

    def __iter__(self):
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
