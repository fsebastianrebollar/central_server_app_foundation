"""Pure helpers — slugify, role hierarchy, upload-name sanitisation.

Everything here is stateless and import-cheap on purpose, so the Flask
blueprint and the store can both import these without dragging the
SQLite or markdown machinery along.
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Optional


# Role hierarchy — higher rank sees everything a lower rank sees.
# "guest" is the implicit minimum (no login); pages with min_role = None
# are visible to everyone.
ROLE_RANK: dict[str, int] = {
    "guest": 0,
    "operator": 1,
    "supervisor": 2,
    "admin": 3,
}


# Pages can only be gated at supervisor or admin level; "operator" is the
# default everyone sees. Kept as a set for O(1) validation.
VALID_MIN_ROLES: set[Optional[str]] = {None, "supervisor", "admin"}


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Convert arbitrary text into a URL-safe slug.

    Strips diacritics, lowercases, collapses anything non-alphanumeric
    into single dashes, and never returns an empty string ("page" is
    the fallback).
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = _SLUG_RE.sub("-", text).strip("-")
    return text or "page"


def _rank(role: Optional[str]) -> int:
    return ROLE_RANK.get(role or "", 0)


def user_can_see(min_role: Optional[str], user_role: Optional[str]) -> bool:
    """True if a user with `user_role` may see a page whose `min_role` is set.

    `min_role=None` means "public" — every role passes, including guests.
    """
    if not min_role:
        return True
    return _rank(user_role) >= _rank(min_role)


_UPLOAD_STRIP_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_upload_name(original: str) -> str:
    """Sanitise a user-supplied filename for safe on-disk storage.

    Strips the path component, normalises unicode, removes anything that
    isn't alnum/`.`/`_`/`-`, and guarantees a non-empty result.
    """
    name = os.path.basename(original or "").strip()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = _UPLOAD_STRIP_RE.sub("_", name).strip("._")
    if not name:
        name = "image"
    return name
