# central-server-app-foundation

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
| `design` | ✅ chassis `base.html` + Sidebar API + chassis.js + floating pill toolbar + settings shell + auth templates (8a+8b+8c+8d) |
| `settings_ui` | ✅ `SettingsShell` section registry + `/settings` section partial + shared `.settings-*` CSS |
| `auth_ui` | ✅ `create_auth_blueprint` factory + `login.html` + `user.html` + `_user_body`/`_user_scripts` partials |
| `i18n` | ✅ `init_babel` + `make_locale_resolver` + bundled es/de catalogs for chassis strings |

See `MONOREPO_PLAN.md` at the repo root for the full extraction plan.

## Install (editable, for local dev)

```bash
pip install -e packages/app-base
```

## Usage — health blueprint

```python
from central_server_app_foundation.contract import create_health_blueprint

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
from central_server_app_foundation.contract import (
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
from central_server_app_foundation.wiki import WikiStore, render_markdown

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
from central_server_app_foundation.settings import SettingsStore

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
from central_server_app_foundation.design import Sidebar, create_design_blueprint

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
{% extends "central_server_app_foundation/design/base.html" %}

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

## Usage — settings shell

```python
from central_server_app_foundation.settings_ui import (
    SettingsShell, SettingsButton, create_settings_blueprint,
)

shell = SettingsShell()
shell.section(
    "cache",
    title="Cache & Service",
    description="Inspect / clear caches, restart the service.",
    buttons=[
        SettingsButton(label="Cache Manager", icon="&#128190;",
                       onclick="openCacheModal()"),
        SettingsButton(label="Service Control", icon="&#9881;",
                       onclick="openServiceModal()"),
    ],
    admin_only=True,     # default; admin-only sections hidden otherwise
)
shell.section(
    "docs",
    title="Docs",
    buttons=[SettingsButton(label="Wiki", href="/wiki")],
    admin_only=False,
)

app.register_blueprint(create_settings_blueprint(
    shell=shell,
    is_admin_resolver=lambda: session.get("is_admin"),          # default
    is_supervisor_resolver=lambda: get_role(user_id) == "supervisor",
))
```

The blueprint injects `chassis_settings_sections` (already filtered by
role) into every template context, so the app's `settings.html`
becomes:

```jinja
{% extends "base.html" %}
{% block content %}
<section class="card">
    <h2>{{ _('Settings') }}</h2>
    {% include "central_server_app_foundation/settings/_sections.html" %}
</section>
{% endblock %}
```

Modals, JS handlers and the backing API endpoints stay in the app —
the chassis only owns the section grid so the visual skeleton is
consistent across apps. Shared button/grid styles ship as
`/settings-static/settings.css`; load it from the app's `base.html`
once, not per-page.

Section gating follows the sidebar convention: admins implicitly pass
supervisor-only gates, and if a role resolver raises, the section is
hidden (safer than leaking admin entries on a bug).

## Usage — auth blueprint + templates

```python
from central_server_app_foundation.auth_ui import create_auth_blueprint
from central_server_app_foundation.auth import UserStore

_store = UserStore(
    db_path=lambda: _AUTH_DB_PATH,
    admin_user="admin",
    admin_pass="changeme",
)

def _on_login(user, session):
    # Hydrate whatever session state the app cares about beyond identity
    # (theme, locale, workspace defaults, …). Runs AFTER user_id / is_admin
    # / role / is_guest are set by the library.
    session["theme"] = _get_pref(user["username"], "theme", "")

auth_bp = create_auth_blueprint(
    user_store=_store,
    post_login_endpoint="main.dashboard",      # where to go after login
    gettext=flask_babel.gettext,               # optional
    supported_languages=("en", "es", "de"),
    allow_guest=True,                          # /login/guest on by default
    get_user_pref=_get_pref,
    set_user_pref=_set_pref,
    on_login_hook=_on_login,
    login_brand_short="CS",                    # shown in login.html
    login_brand_full="Conter Stats",
    login_stylesheet_urls=(("static", "css/style.css"),),
    login_favicon_url=("static", "img/favicon.ico"),
    user_template="user.html",                 # override to keep app chrome
    protected_user="admin",                    # hides delete/role buttons
)
app.register_blueprint(auth_bp)
```

The blueprint is always named `auth`, so `url_for("auth.login")` /
`url_for("auth.user_profile")` / `url_for("auth.set_theme")` /
`url_for("auth.set_language")` call sites keep working.

Endpoints mounted:

- `GET|POST /login`, `GET /login/guest`, `POST /logout`
- `GET /user`, `POST /change-password`
- `POST /admin/users/create`, `POST /admin/users/<u>/delete`,
  `POST /admin/users/<u>/role`, `POST /admin/users/<u>/change-password`
- `POST /api/user/change-password`, plus JSON variants of every admin
  form action above under `/api/admin/users/…`
- `POST /api/theme`, `GET /lang/<lang>`

Login chrome URLs can be either a plain string (used as-is) or a
`(endpoint, filename)` tuple — tuples resolve through `url_for` at
request time, so `APPLICATION_ROOT` prefixing (v1.3 reverse-proxy
deployments) works transparently.

### Template shape

`login.html` is a standalone page owned by the library; apps only
configure its chrome via the blueprint factory. `user.html` extends
`central_server_app_foundation/design/base.html` and is drop-in for apps that don't
need custom header widgets. Apps that do (product picker, workspace
widget, etc.) keep their own `user.html` template and `{% include %}`
the library's body + scripts partials:

```jinja
{% extends "base.html" %}
{% block content %}
{% include "central_server_app_foundation/auth/_user_body.html" %}
{% endblock %}
{% block scripts %}
{% include "central_server_app_foundation/auth/_user_scripts.html" %}
{% endblock %}
```

The user body partial reads `is_admin`, `is_guest` and `auth_protected_user`
from the template context — apps already providing the first two through
a global `context_processor` don't need to do anything extra; the third
is injected by the auth blueprint.

## Usage — pill toolbar

A floating bottom-center pill used for view/mode switching and
per-page selectors (report product, time view mode, etc.). The
blueprint serves both the JS module and the CSS at
`/design-static/pill-toolbar.{js,css}`. Load them from the app
template:

```jinja
{% block app_styles %}
    <link rel="stylesheet"
          href="{{ url_for('design.static', filename='pill-toolbar.css') }}">
{% endblock %}

{% block pre_scripts %}
    <script src="{{ url_for('design.static', filename='pill-toolbar.js') }}"></script>
{% endblock %}
```

Then create a toolbar instance with `PillToolbar.create(opts)`:

```html
<div class="view-toolbar"><div id="my-pill" class="view-toolbar-pill"></div></div>

<script>
const tb = PillToolbar.create({
    mount: '#my-pill',
    items: [
        { value: 'table', label: 'Table', icon: '▦' },
        { value: 'time',  label: 'Time',  icon: '⏱' },
        { value: 'logic', label: 'Logic', icon: '⇢' },
    ],
    value: 'table',
    onChange: (v) => { /* render... */ },
    // optional persistence layers — pick one that fits the use case:
    urlParam:   'product',   // ?product=<v>
    hashKey:    'mode',      // #mode=<v>  (or bare  #value)
    storageKey: 'my.view',   // localStorage
});
// tb.setValue(v), tb.getValue(), tb.setItems([...]), tb.setVisible(bool), tb.destroy()
</script>
```

Initial value resolution order (first match wins): `urlParam` →
`hashKey` → `storageKey` → `opts.value`. The component listens on
`hashchange` so external hash rewrites keep the toolbar in sync.

Theming pulls from the chassis CSS variables (`--bg-surface`,
`--border`, `--text`, `--text-secondary`, `--neon`, `--neon-subtle`),
so any app that already consumes the design chassis gets the right
look without extra work.

## Usage — i18n

```python
from central_server_app_foundation.i18n import init_babel, make_locale_resolver

SUPPORTED_LANGS = ("en", "es", "de")

get_locale = make_locale_resolver(
    supported_languages=SUPPORTED_LANGS, default_language="en",
)

init_babel(
    app,
    supported_languages=SUPPORTED_LANGS,
    default_language="en",
    translation_dirs=("translations",),  # app's own catalogs
    locale_selector=get_locale,
)
```

The library prepends its own `translations/` directory to the Flask-Babel
search path, so a string like `"User Profile"` resolves against the
bundled chassis catalog (es/de provided) when the app hasn't
re-translated it. Apps only need to translate their domain strings.

`make_locale_resolver()` returns a function safe to call outside a
request context (returns the default language), which keeps service-layer
code wrapping error messages with `gettext()` safe in background jobs.

### Adding strings to the library catalog

From `packages/app-base/`:

```bash
pybabel extract -F central_server_app_foundation/i18n/babel.cfg \
    -o central_server_app_foundation/i18n/translations/messages.pot central_server_app_foundation
pybabel update -i central_server_app_foundation/i18n/translations/messages.pot \
    -d central_server_app_foundation/i18n/translations
# edit es/de .po files, then:
pybabel compile -d central_server_app_foundation/i18n/translations
```

## Tests

```bash
python -m pytest packages/app-base/tests/
```
