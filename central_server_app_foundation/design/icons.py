"""Standard icon set for Conter chassis sidebar tabs and UI widgets.

All values are single Unicode characters rendered inside a
`.sidebar-icon` span via Jinja's `|safe` filter, or used inline in
any HTML context. Using named constants avoids copy-pasting numeric
HTML entities throughout app code.

Usage::

    from central_server_app_foundation.design import ChassisIcons as I

    sidebar.entry("Dashboard", endpoint="main.dashboard", icon=I.DASHBOARD)
    sidebar.entry("Wiki",      endpoint="wiki.index",     icon=I.WIKI)
    sidebar.entry("Settings",  endpoint="main.settings",  icon=I.SETTINGS, admin_only=True)
"""


class ChassisIcons:
    # ── Sidebar tabs ──────────────────────────────────────────────────────────
    DASHBOARD = "■"   # ■  solid square
    SEARCH    = "⌕"   # ⌕  crosshair / search
    REPORTS   = "☰"   # ☰  trigram — list / reports
    WIKI      = "☶"   # ☶  trigram mountain — knowledge base
    SETTINGS  = "⚙"   # ⚙  gear
    USERS     = "◉"   # ◉  fisheye — people / profile

    # ── Buttons and inline widgets ────────────────────────────────────────────
    EDIT      = "✎"   # ✎  pencil
    ADD       = "+"   # +  plus
    CLOSE     = "✕"   # ✕  multiply / close
    REFRESH   = "↺"   # ↺  counterclockwise arrow
    DOWNLOAD  = "⤓"   # ⤓  downward arrow into box
    UPLOAD    = "⤒"   # ⤒  upward arrow from box
    INFO      = "ℹ"   # ℹ  information
