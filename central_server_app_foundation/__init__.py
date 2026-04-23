"""Central Server App Foundation — shared chassis for internal apps.

Each Conter app (conter-stats, ini-configurator, …) consumes this package
to get the supervisor contract, auth, wiki, settings, and design system
for free. Only domain-specific routes, services and templates stay in
the app repo.

Modules:

- contract.health    — /health /version /icon /shutdown blueprint factory
- contract.cli       — argparse helpers for --headless/--prefix/--info/…
- contract.data_paths — CONTER_DATA_DIR resolver
- version            — bundled-version-file + pyproject reader + uptime
- auth               — UserStore class (SQLite + roles + bootstrap admin)
- wiki               — WikiStore (tree + locales + uploads) + markdown renderer
- settings           — SettingsStore (two-scope SQLite key/value + JSON helpers)
- design             — chassis base.html + Sidebar API + chassis.js
                      + floating pill toolbar + settings-shell section
                      registration
- settings_ui        — SettingsShell / SettingsSection / SettingsButton
                      + /settings section partial + shared settings.css
- auth_ui            — create_auth_blueprint + login.html + user.html
                      + _user_body/_user_scripts partials
- i18n               — init_babel + make_locale_resolver + bundled
                      es/de catalogs for chassis strings
"""

__version__ = "0.1.0"
