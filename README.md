# conter-app-base

Shared chassis for Conter internal apps. Each consumer (conter-stats,
ini-configurator, …) registers a few factory-built blueprints and
declares its own sidebar tabs; everything else (supervisor contract,
auth, wiki, settings UI, design system, i18n) comes from here.

## Current status

| Module | Status |
|---|---|
| `contract.health` | ✅ `/health`, `/version`, `/icon`, `/shutdown` |
| `contract.cli` | ✅ argparse scaffold + env propagation |
| `contract.data_paths` | ✅ `CONTER_DATA_DIR` resolver |
| `version` | ✅ bundled-version + pyproject reader + uptime |
| `auth` | ✅ `UserStore` (SQLite + roles + bootstrap admin) |
| `wiki` | ✅ `WikiStore` (tree + locales + uploads) + markdown renderer |
| `settings` | ✅ `SettingsStore` (two-scope SQLite key/value + JSON helpers) |
| `design` | ⏳ base.html + sidebar API + style.css |
| `i18n` | ⏳ Babel wiring + merged catalogs |

See `MONOREPO_PLAN.md` at the repo root for the full extraction plan.

## Install (editable, for local dev)

```bash
pip install -e packages/app-base
```

## Usage — health blueprint

```python
from conter_app_base.contract import create_health_blueprint

health_bp = create_health_blueprint(
    app_name="my-app",
    app_display_name="My App",
    app_description="What this app does, shown in the central portal.",
    contract_version="1.3",
    get_version=lambda: "1.0.0",
    get_build_date=lambda: "2026-04-21T00:00:00Z",
    get_uptime_seconds=lambda: int(time.time() - _start),
    db_probe=_my_db_probe,                  # returns "ok" | "error" | "n/a"
    icon_path="path/to/icon.png",           # or a callable returning a path
)
app.register_blueprint(health_bp)
```

The returned blueprint is named `health`, so endpoints are:

- `health.health_check` → `GET /health`
- `health.version_info` → `GET /version`
- `health.icon`         → `GET /icon`
- `health.shutdown`     → `POST /shutdown`

Apps that expose an auth gate should list these four names in their
`PUBLIC_ENDPOINTS` set so the supervisor can poll them without a session.

## Usage — CLI scaffold

```python
from conter_app_base.contract import (
    build_parser, handle_preboot_flags, apply_contract_env,
)

parser = build_parser(description="My App — Web & Desktop")
parser.add_argument("--desktop", action="store_true")   # app-specific
args = parser.parse_args()

handle_preboot_flags(            # exits 0 for --version / --info
    args,
    get_version=get_version,
    app_name=APP_NAME,
    display_name=APP_DISPLAY_NAME,
    description=APP_DESCRIPTION,
    contract_version=CONTRACT_VERSION,
)

apply_contract_env(args)         # sets CONTER_* env from args
from app import create_app
app = create_app()               # safe: env is primed before import
```

`build_parser()` ships every contract flag (`--headless`, `--host`,
`--port`, `--log-level`, `--data-dir`, `--shutdown-token`, `--prefix`,
`--info`, `--version`) so apps only declare what's domain-specific.

## Usage — wiki

```python
from conter_app_base.wiki import WikiStore, render_markdown

_store = WikiStore(
    db_path=lambda: _DB_PATH,            # late binding for tests
    uploads_dir=lambda: UPLOADS_DIR,
    locale_resolver=_current_locale,     # returns "en" | "es" | "de"
    gettext=flask_babel.gettext,         # optional, identity default
)

init_wiki_db   = _store.init_schema
list_tree      = _store.list_tree
get_page       = _store.get_page
create_page    = _store.create_page
save_upload    = _store.save_upload
# ... etc.

def seed_initial_content():
    # Wiki content is per-app — the library only owns the machinery.
    from app.services.wiki_seed_content import ARTICLES
    return _store.seed(ARTICLES)
```

`render_markdown(text, url_prefix=...)` is a pure function: pass
`url_prefix=APPLICATION_ROOT` when the app runs behind the
central-server reverse proxy (contract v1.3) so hardcoded
`/api/wiki/uploads/...` image URLs in seed content survive the
prefix rewrite.

## Usage — settings

```python
from conter_app_base.settings import SettingsStore

_store = SettingsStore(db_path=lambda: _DB_PATH)   # late binding for tests

_connect       = _store._connect
get_user_pref  = _store.get_user_pref
set_user_pref  = _store.set_user_pref
get_global     = _store.get_global
set_global     = _store.set_global

# App-specific domain helpers stay in the app — they are just thin JSON
# wrappers on top of the store.
def get_column_config(table: str) -> list[str]:
    return _store.get_global_json(f"columns_{table}", DEFAULTS[table])

def set_column_config(table: str, columns: list[str]) -> None:
    _store.set_global_json(f"columns_{table}", columns)
```

Two scopes, one SQLite file:

- **`global_settings`** — one value per key, shared across users.
  Column defaults, chart defaults, DB connection, i18n preferences.
- **`user_preferences`** — one value per (username, key), per-user
  overrides. Theme, sidebar state, locale.

Every connection runs `PRAGMA journal_mode=WAL` and auto-creates both
tables (`CREATE TABLE IF NOT EXISTS`), so any subsystem reaching the DB
first (auth, wiki, settings) finds what it needs without caring about
init order. `get_global_json` / `set_global_json` replace the
`json.loads(get_global(k, "")) or default` boilerplate apps would
otherwise repeat around every typed getter.

## Tests

```bash
python -m pytest packages/app-base/tests/
```
