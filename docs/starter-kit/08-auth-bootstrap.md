# 08 · Auth con admin bootstrap

Patrón de autenticación con roles (`admin`, `supervisor`, `user`), guest login (solo lectura), admin hardcoded inicial, y dev auto-login.

## `app/services/auth_service.py`

```python
import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


_DB_PATH = None  # Monkeypatched in tests

# Bootstrap admin — changeable but remember that the hash in DB persists
_ADMIN_USER = "admin"
_ADMIN_PASS = "change-me-now"

VALID_ROLES = ("user", "supervisor", "admin")


def _resolve_db_path() -> str:
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = os.path.join(os.environ["APPDATA"], "My App")
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support/My App")
        else:
            base = os.path.expanduser("~/.my-app")
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "auth.db")


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = _resolve_db_path()
    return _DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username   TEXT PRIMARY KEY,
                pwhash     TEXT NOT NULL,
                role       TEXT NOT NULL DEFAULT 'user',
                is_admin   INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Bootstrap admin if table is empty / missing him
        row = c.execute(
            "SELECT 1 FROM users WHERE username = ?", (_ADMIN_USER,)
        ).fetchone()
        if not row:
            c.execute(
                "INSERT INTO users (username, pwhash, role, is_admin) "
                "VALUES (?, ?, 'admin', 1)",
                (_ADMIN_USER, generate_password_hash(_ADMIN_PASS)),
            )


def authenticate(username: str, password: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT username, pwhash, role, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not row or not check_password_hash(row["pwhash"], password):
        return None
    return {
        "username": row["username"],
        "role":     row["role"],
        "is_admin": bool(row["is_admin"]),
    }


def create_user(username: str, password: str, role: str = "user") -> None:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")
    is_admin = 1 if role == "admin" else 0
    with _conn() as c:
        c.execute(
            "INSERT INTO users (username, pwhash, role, is_admin) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), role, is_admin),
        )


def delete_user(username: str) -> None:
    if username == _ADMIN_USER:
        raise ValueError("Cannot delete bootstrap admin")
    with _conn() as c:
        c.execute("DELETE FROM users WHERE username = ?", (username,))


def set_role(username: str, role: str) -> None:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")
    if username == _ADMIN_USER and role != "admin":
        raise ValueError("Cannot demote bootstrap admin")
    is_admin = 1 if role == "admin" else 0
    with _conn() as c:
        c.execute(
            "UPDATE users SET role = ?, is_admin = ? WHERE username = ?",
            (role, is_admin, username),
        )


def change_password(username: str, new_password: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE users SET pwhash = ? WHERE username = ?",
            (generate_password_hash(new_password), username),
        )


def list_users() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT username, role, is_admin FROM users ORDER BY username"
        ).fetchall()
    return [dict(r) for r in rows]


def can_publish(role: str) -> bool:
    """Supervisor+ gate. Use this helper in endpoints that need elevated permissions."""
    return role in ("supervisor", "admin")
```

## `app/routes/auth.py`

```python
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, jsonify
from app.services import auth_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = auth_service.authenticate(
            request.form["username"],
            request.form["password"],
        )
        if not user:
            flash("Invalid credentials")
            return redirect(url_for("auth.login"))
        session["user_id"]  = user["username"]
        session["is_admin"] = user["is_admin"]
        session["role"]     = user["role"]
        session["is_guest"] = False
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@auth_bp.get("/login/guest")
def login_guest():
    session.clear()
    session["user_id"]  = "guest"
    session["is_admin"] = False
    session["is_guest"] = True
    session["role"]     = "user"
    return redirect(url_for("main.dashboard"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.post("/change-password")
def change_password():
    if session.get("is_guest"):
        flash("Guests cannot change password")
        return redirect(url_for("main.dashboard"))

    current = request.form["current_password"]
    new     = request.form["new_password"]
    confirm = request.form["confirm_password"]

    if new != confirm:
        flash("Passwords don't match")
        return redirect(url_for("main.profile"))

    # Verify current
    if not auth_service.authenticate(session["user_id"], current):
        flash("Current password incorrect")
        return redirect(url_for("main.profile"))

    auth_service.change_password(session["user_id"], new)
    flash("Password changed")
    return redirect(url_for("main.profile"))


@auth_bp.post("/admin/users/create")
def admin_create_user():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403
    try:
        auth_service.create_user(
            request.form["username"],
            request.form["password"],
            request.form.get("role", "user"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@auth_bp.post("/admin/users/<username>/delete")
def admin_delete_user(username):
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403
    try:
        auth_service.delete_user(username)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@auth_bp.post("/admin/users/<username>/role")
def admin_set_role(username):
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403
    try:
        auth_service.set_role(username, request.form["role"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})
```

## Gate en `before_request`

```python
# app/__init__.py
PUBLIC_ENDPOINTS = {
    "auth.login",
    "auth.login_guest",
    "static",
}


@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    if session.get("user_id"):
        return None
    if app.config["DEV_MODE"]:   # True when not sys.frozen
        session["user_id"]  = _ADMIN_USER
        session["is_admin"] = True
        session["is_guest"] = False
        session["role"]     = "admin"
        return None
    return redirect(url_for("auth.login"))
```

## Uso en endpoints

### Admin-only

```python
if not session.get("is_admin"):
    return jsonify({"error": "Admin only"}), 403
```

### Supervisor-or-admin

```python
from app.services.auth_service import can_publish

if not can_publish(session.get("role", "user")):
    return jsonify({"error": "Supervisor required"}), 403
```

### Block guests

```python
if session.get("is_guest"):
    return jsonify({"error": "Guests cannot do this"}), 403
```

## Dev auto-login

Cuando `not sys.frozen` (i.e. ejecutando `python run.py`), el `before_request` inyecta admin automáticamente. En el binario PyInstaller (`sys.frozen == True`), el user debe loguear.

Consecuencia: nunca pidas login en dev, nunca saltes login en producción.

## Rotar el admin bootstrap

```python
_ADMIN_PASS = "new-secure-password"
```

**Importante**: cambiar la constante NO re-hashea el password guardado. El user "admin" ya existe en la DB con el hash viejo. Para rotar:

1. Cambia `_ADMIN_PASS` en el código.
2. Borra `auth.db` (o elimina solo al user admin).
3. Próximo arranque, `init_db()` recrea el admin con el hash nuevo.

Alternativa: desde la UI, loguea como admin con la password vieja → cambia password desde profile.

## Reglas de seguridad

- ✅ Passwords hasheadas con `werkzeug.security` (scrypt por defecto).
- ✅ `session` firmada con `SECRET_KEY`. **`SECRET_KEY` en producción debe venir de env var**, nunca hardcoded.
- ✅ Guest endpoints explícitos, check_password_hash usa timing-safe comparison.
- ❌ Sin 2FA. Si la app sale fuera de red privada, considera TOTP.
- ❌ Sin rate limiting. Añade `Flask-Limiter` si el `/login` queda expuesto.
- ❌ Sin CSRF explícito. Flask-WTF lo añade; para este patrón simple no es crítico pero piénsalo si aceptas uploads.
