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
| `version` | ⏳ bundled-version + pyproject reader |
| `auth` | ⏳ users, roles, login/logout |
| `wiki` | ⏳ articles + markdown rendering |
| `settings` | ⏳ pluggable sections UI |
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

## Tests

```bash
python -m pytest packages/app-base/tests/
```
