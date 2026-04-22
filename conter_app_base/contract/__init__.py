"""Supervisor contract glue (conter_central_server v1.3).

Each piece is a factory: the app supplies its own identity (name,
display_name, description) and callbacks (db_probe, get_version, …)
and gets back a wired Flask blueprint or an argparse-ready set of
flags.
"""
from conter_app_base.contract.cli import (
    VALID_LOG_LEVELS,
    apply_contract_env,
    build_parser,
    handle_preboot_flags,
    normalize_prefix,
)
from conter_app_base.contract.health import create_health_blueprint

__all__ = [
    "create_health_blueprint",
    "build_parser",
    "handle_preboot_flags",
    "apply_contract_env",
    "normalize_prefix",
    "VALID_LOG_LEVELS",
]
