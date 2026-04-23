# 01 · Flask factory

Patrón `create_app()` con blueprints, before_request para auth gate, y context processor para exponer user/theme a templates.

## `app/__init__.py`

```python
import os
import sys
import atexit
from flask import Flask, session, request, has_request_context

from app.routes.main import main_bp
from app.routes.api import api_bp
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.services import auth_service, settings_service


PUBLIC_ENDPOINTS = {
    "auth.login",
    "auth.login_guest",
    "static",
}


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-in-prod")
    app.config["DEV_MODE"] = not getattr(sys, "frozen", False)

    # Initialize local DBs (auto-migrate via _init_db in each service)
    settings_service.init_db()
    auth_service.init_db()

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    @app.before_request
    def require_login():
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if request.endpoint and request.endpoint.startswith("static"):
            return None
        if session.get("user_id"):
            return None
        # Dev auto-login
        if app.config["DEV_MODE"]:
            session["user_id"] = "admin"
            session["is_admin"] = True
            session["is_guest"] = False
            return None
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_user():
        return {
            "current_user": session.get("user_id"),
            "is_admin":     session.get("is_admin", False),
            "is_guest":     session.get("is_guest", False),
            "user_theme":   session.get("theme", ""),
        }

    # Graceful shutdown: dump caches etc.
    if not _in_pytest():
        atexit.register(_on_exit)

    return app


def _in_pytest() -> bool:
    return "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST")


def _on_exit():
    # from app.services.keys_cache import dump_to_disk
    # dump_to_disk()
    pass
```

## Adaptaciones

- **Blueprints**: crea `main_bp`, `api_bp`, `admin_bp`, `auth_bp` en `app/routes/`. Dividir por rol (rutas públicas vs admin vs API JSON) escala mejor que un mega-blueprint.
- **`PUBLIC_ENDPOINTS`**: lista blanca explícita. Nunca pongas aquí `"/api/*"` completo — es demasiado amplio.
- **`DEV_MODE`**: `not sys.frozen` distingue "ejecutando en Python" vs "ejecutando desde el binario PyInstaller". Auto-login solo en dev.
- **`SECRET_KEY`**: en producción, `SECRET_KEY=xxx python run.py`. Nunca hardcodear algo no-dev.

## `app/routes/main.py` — blueprint mínimo

```python
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
```

## `app/templates/base.html` — layout mínimo

```jinja
<!DOCTYPE html>
<html lang="{{ current_lang|default('en') }}" data-theme="{{ user_theme or 'dark' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}My App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        {% if current_user %}
            Signed in as <strong>{{ current_user }}</strong>
            {% if is_admin %}<span class="badge">admin</span>{% endif %}
        {% endif %}
    </header>
    <main>{% block content %}{% endblock %}</main>
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

## Notas

- **Orden de init**: registra blueprints **después** de `init_db()` de los servicios. Si un blueprint importa un servicio cuya DB no existe, puede petar al primer request (solo en casos borde).
- **`app.config["DEV_MODE"]`** se lee desde templates como `{{ config.DEV_MODE }}` si quieres mostrar un banner "DEV" en el UI.
- **No uses `debug=True`** en producción; se controla con `use_reloader=False` en el runtime desktop (ver [03-dual-runtime](03-dual-runtime.md)).
