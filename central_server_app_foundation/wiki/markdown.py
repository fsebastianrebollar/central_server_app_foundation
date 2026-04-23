"""Markdown rendering for wiki pages.

Trusted pipeline — only admins can edit wiki content, so raw HTML in the
source markdown is intentional (screenshots with alt text, tables with
colgroups, etc.). No bleach pass.
"""
from __future__ import annotations

import markdown as md


# Extensions shared by every Conter app:
# - fenced_code       ```lang blocks
# - tables            GFM-style pipe tables
# - toc               anchor IDs on headings (so deep-links work)
# - sane_lists        better list nesting
# - attr_list         {: .class} attrs on inline elements
# - nl2br             soft line breaks render as <br> (wiki editors
#                     expect paragraphs without blank lines)
_MD_EXTENSIONS = [
    "fenced_code",
    "tables",
    "toc",
    "sane_lists",
    "attr_list",
    "nl2br",
]


def render_markdown(text: str, *, url_prefix: str = "") -> str:
    """Render markdown to HTML.

    `url_prefix` rewrites hardcoded `/api/wiki/uploads/...` image URLs
    so the wiki survives deployment behind the central-server reverse
    proxy (contract v1.3). Seed content can't use `url_for()` because
    markdown is rendered outside any request context, so the prefix is
    injected here as a pure string substitution.
    """
    if not text:
        return ""
    html = md.markdown(text, extensions=_MD_EXTENSIONS, output_format="html5")
    prefix = (url_prefix or "").rstrip("/")
    if prefix:
        html = html.replace(
            '"/api/wiki/uploads/',
            '"' + prefix + '/api/wiki/uploads/',
        )
    return html
