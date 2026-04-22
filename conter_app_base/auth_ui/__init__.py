"""Shared auth blueprint for Conter apps.

Ships the `/login`, `/logout`, `/user`, `/change-password`,
`/admin/users/...`, `/api/...`, `/api/theme` and `/lang/<lang>` routes
as a Flask blueprint factory, plus the `login.html` page and the
`_user_body.html` / `_user_scripts.html` partials the app drops into
its own user profile template.

The factory is callback-heavy because identity concerns are orthogonal
from the pref stores apps use for theme / language / workspace state —
the library sets identity session keys (`user_id`, `is_admin`,
`is_guest`, `role`) and hands off to `on_login_hook(user, session)` so
each app hydrates whatever else it wants.
"""
from __future__ import annotations

from .blueprint import create_auth_blueprint

__all__ = ["create_auth_blueprint"]
