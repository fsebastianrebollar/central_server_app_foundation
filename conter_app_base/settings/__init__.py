"""Settings chassis — generic JSON-aware key/value store on SQLite.

Every Conter app needs the same two scopes of persistent config:

- **Global settings** — one value per key, shared across users.
  Typical uses: column defaults, chart defaults, DB connection,
  scheduled-report config, i18n preferences.
- **User preferences** — one value per (username, key), per-user
  overrides. Typical uses: theme, sidebar state, locale.

`SettingsStore` ships the SQL for both, plus JSON convenience
helpers so apps can stop writing `json.dumps` / `json.loads`
boilerplate around every domain getter.

Canonical usage (see `app/services/settings_service.py` in
conter-stats for a working example):

    from conter_app_base.settings import SettingsStore

    _store = SettingsStore(db_path=lambda: _DB_PATH)

    _connect       = _store._connect
    get_user_pref  = _store.get_user_pref
    set_user_pref  = _store.set_user_pref
    get_global     = _store.get_global
    set_global     = _store.set_global

    # App-specific domain helpers stay in the app — they are just
    # thin JSON wrappers on top of the store.
    def get_column_config(table: str) -> list[str]:
        return _store.get_global_json(f"columns_{table}", DEFAULTS[table])

    def set_column_config(table: str, columns: list[str]) -> None:
        _store.set_global_json(f"columns_{table}", columns)
"""
from conter_app_base.settings.store import SettingsStore

__all__ = ["SettingsStore"]
