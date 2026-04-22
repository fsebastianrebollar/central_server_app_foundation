"""Conter App Base — shared chassis for internal apps.

Each Conter app (conter-stats, ini-configurator, …) consumes this package
to get the supervisor contract, auth, wiki, settings, and design system
for free. Only domain-specific routes, services and templates stay in
the app repo.

Current extraction status (see MONOREPO_PLAN.md at the repo root):

- [x] contract.health    — /health /version /icon /shutdown blueprint factory
- [x] contract.cli       — argparse helpers for --headless/--prefix/--info/…
- [x] contract.data_paths — CONTER_DATA_DIR resolver
- [ ] version            — bundled-version-file + pyproject reader + uptime
- [ ] auth               — users, roles, login/logout routes, templates
- [ ] wiki               — articles, seed hook, markdown rendering
- [ ] settings           — pluggable sections UI
- [ ] design             — base.html + sidebar API + style.css + modals
- [ ] i18n               — Babel wiring + merged catalog

Incrementally extracted from conter-stats; each extraction should ship
as a standalone commit so the history shows how the chassis grows.
"""

__version__ = "0.1.0"
