"""Entry point for Template App.

Usage:
    python -m template_app.run
    python -m template_app.run --port 5001
    python -m template_app.run --host 0.0.0.0 --port 8080
    python -m template_app.run --data-dir /var/data/template
    python -m template_app.run --info
    python -m template_app.run --version

The contract CLI flags (--headless, --host, --port, --log-level, --data-dir,
--shutdown-token, --prefix, --info, --version) are declared by the chassis.
Do NOT re-declare them here; add only app-specific flags.
"""
import time

_START = time.time()

from pathlib import Path

from central_server_app_foundation.contract import (
    apply_contract_env,
    build_parser,
    handle_preboot_flags,
)
from central_server_app_foundation.version import resolve_build_date, resolve_version

_PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"

APP_NAME = "template-app"
APP_DISPLAY_NAME = "Template App"
APP_DESCRIPTION = "Reference integration of central_server_app_foundation."
CONTRACT_VERSION = "1.3"

if __name__ == "__main__":
    parser = build_parser(
        description=f"{APP_DISPLAY_NAME} — Web",
        default_host="127.0.0.1",
        default_port=5000,
    )
    # Add app-specific flags here, e.g.:
    # parser.add_argument("--my-flag", help="...")
    args = parser.parse_args()

    # Handles --version (print + exit) and --info (print JSON + exit).
    # Must run before Flask is imported.
    handle_preboot_flags(
        args,
        get_version=lambda: resolve_version(_PYPROJECT),
        app_name=APP_NAME,
        display_name=APP_DISPLAY_NAME,
        description=APP_DESCRIPTION,
        contract_version=CONTRACT_VERSION,
    )

    # Propagates CLI flags → CONTER_* env vars before create_app() runs.
    apply_contract_env(args)

    from template_app.app import create_app

    app = create_app(start_time=_START)
    app.run(host=args.host, port=args.port, debug=False)
