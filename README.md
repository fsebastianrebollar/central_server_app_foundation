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
| `design` | 🟡 chassis `base.html` + Sidebar API + chassis.js (8a done; pill toolbar, settings shell, auth templates pending as 8b–8d) |
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

## Usage — design chassis

```python
from conter_app_base.design import Sidebar, create_design_blueprint

sb = Sidebar()
sb.entry("Dashboard", endpoint="main.dashboard",
         icon="&#9632;", hide_for_guests=True)
sb.entry("Reports",   endpoint="main.reports", icon="&#9776;",
         hide_for_guests=True,
         active_endpoints={"main.reports", "main.reports_daily",
                           "main.reports_monthly"})
sb.entry("Search",    endpoint="main.index", icon="&#8981;")
sb.entry("Settings",  endpoint="main.settings",
         icon="&#9881;", admin_only=True)

app.register_blueprint(create_design_blueprint(
    sidebar=sb,
    brand_short="CS",
    brand_full="Conter Stats",
    brand_endpoint="main.dashboard",
    user_profile_endpoint="auth.user_profile",
    logout_endpoint="auth.logout",
    language_switch_endpoint="auth.set_language",
    supported_languages=("en", "es", "de"),
    theme_save_url="/api/theme",
))
```

Then in the app's `base.html`:

```jinja
{% extends "conter_app_base/design/base.html" %}

{% block header_extra_widgets %}
    {# product picker, workspace widget, etc. #}
{% endblock %}

{% block pre_scripts %}
    {# app-specific JS that must run before chassis.js #}
{% endblock %}

{% block scripts %}
    {# app-specific JS that runs after chassis.js #}
{% endblock %}
```

Available blocks:

| Block | Purpose |
|---|---|
| `title` | page title (default: `chassis_brand.full`) |
| `app_styles` | stylesheet(s) + favicon |
| `head` | extra `<head>` tags (per-page metas, etc.) |
| `header_extra_widgets` | widgets injected to the right of the brand |
| `sidebar_bottom_extra` | extra items below the user pill in the sidebar |
| `content` | main page content |
| `modals_extra` | extra modal markup at the end of `<body>` |
| `pre_scripts` | `<script>` tags loaded *before* chassis.js |
| `scripts` | `<script>` tags loaded *after* chassis.js |

`chassis.js` owns theme toggle, sidebar drawer (desktop persist /
mobile overlay) and the global ESC handler. The theme POST target is
read from `window.APP_THEME_SAVE_URL` (set by the template from
`theme_save_url`), so apps with a non-default endpoint just pass it
to `create_design_blueprint()`.

The `Sidebar.entry()` API supports:

- `icon=` — raw HTML/SVG/entity, rendered with `|safe`.
- `admin_only=`, `supervisor_only=`, `hide_for_guests=` — role gates.
- `active_endpoints=` — set of Flask endpoint names that highlight
  this tab (default: `{endpoint}`).
- `active_when=fn(endpoint, request) -> bool` — custom predicate for
  cases the endpoint set can't express (e.g. "Dashboard tab active
  when the steps page was reached *from* the dashboard").

## Tests

```bash
python -m pytest packages/app-base/tests/
```
