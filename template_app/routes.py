"""Template App — domain blueprint.

The /template route is the only "real" page of this app. It demonstrates:
  - Auth guard (redirect to login when unauthenticated)
  - Reading a global setting from SettingsStore
  - A JSON API endpoint that saves a setting (used by the welcome-message modal)
"""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from central_server_app_foundation.settings import SettingsStore

_WELCOME_KEY = "welcome_message"
_WELCOME_DEFAULT = "Welcome to Template App! Replace this with your domain content."


def create_template_blueprint(*, settings_store: SettingsStore) -> Blueprint:
    bp = Blueprint(
        "template",
        __name__,
        template_folder="templates",
    )

    @bp.route("/")
    def index():
        return redirect(url_for("template.template_page"))

    @bp.route("/template")
    def template_page():
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))

        welcome_msg = settings_store.get_global(_WELCOME_KEY, default=_WELCOME_DEFAULT)
        return render_template("template/index.html", welcome_msg=welcome_msg)

    @bp.route("/api/template/welcome", methods=["POST"])
    def save_welcome():
        """Save the welcome message. Admin-only JSON endpoint."""
        if not session.get("is_admin"):
            return jsonify({"error": "Admin only."}), 403
        data = request.get_json(force=True) or {}
        msg = data.get("message", "").strip()
        if not msg:
            return jsonify({"error": "Message cannot be empty."}), 400
        settings_store.set_global(_WELCOME_KEY, msg)
        return jsonify({"ok": True})

    return bp
