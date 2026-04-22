"""Conter App Base — shared chassis for internal apps.

Each Conter app (conter-stats, ini-configurator, …) consumes this package
to get the supervisor contract, auth, wiki, settings, and design system
for free. Only domain-specific routes, services and templates stay in
the app repo.

Current extraction status (see MONOREPO_PLAN.md at the repo root):

- [x] contract.health    — /health /version /icon /shutdown blueprint factory
- [x] contract.cli       — argparse helpers for --headless/--prefix/--info/…
- [x] contract.data_paths — CONTER_DATA_DIR resolver
- [x] version            — bundled-version-file + pyproject reader + uptime
- [x] auth               — UserStore class (SQLite + roles + bootstrap admin)
- [x] wiki               — WikiStore (tree + locales + uploads) + markdown renderer
- [x] settings           — SettingsStore (two-scope SQLite key/value + JSON helpers)
- [~] design             — chassis base.html + Sidebar API + chassis.js
                          + floating pill toolbar (8a+8b landed; settings
                          shell + auth templates pending as 8c/8d)
- [ ] i18n               — Babel wiring + merged catalog

Incrementally extracted from conter-stats; each extraction should ship
as a standalone commit so the history shows how the chassis grows.
"""

__version__ = "0.1.0"
