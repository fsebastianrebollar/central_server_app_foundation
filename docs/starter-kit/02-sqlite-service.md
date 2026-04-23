# 02 · Patrón de servicio SQLite

Todo servicio que persiste estado local sigue el mismo patrón: **`_DB_PATH` monkeypatcheable**, **`_init_db()` auto-migrate idempotente**, funciones de alto nivel que abren conexión fresca, hacen su query, y cierran.

## Template

```python
# app/services/settings_service.py
import os
import sys
import json
import sqlite3
from typing import Any


_DB_PATH = None  # resolved lazily; overridden by tests via monkeypatch


def _resolve_db_path() -> str:
    if getattr(sys, "frozen", False):
        # Running from PyInstaller bundle
        if sys.platform == "win32":
            base = os.path.join(os.environ["APPDATA"], "My App")
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support/My App")
        else:
            base = os.path.expanduser("~/.my-app")
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "settings.db")


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = _resolve_db_path()
    return _DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Idempotent schema migration. Run at app startup."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                username TEXT NOT NULL,
                key      TEXT NOT NULL,
                value    TEXT,
                PRIMARY KEY (username, key)
            )
        """)
        # New columns go here as ALTER TABLE ... IF NOT EXISTS in SQLite via pragma check:
        _ensure_column(c, "settings", "updated_at", "TEXT")


def _ensure_column(c: sqlite3.Connection, table: str, column: str, type_: str) -> None:
    cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_}")


def get_setting(key: str, default: Any = None) -> Any:
    with _conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return row["value"]


def set_setting(key: str, value: Any) -> None:
    payload = json.dumps(value) if not isinstance(value, str) else value
    with _conn() as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, payload),
        )
```

## Por qué este patrón

### `_DB_PATH` como módulo global

Permite que los tests lo **monkeypatcheen** a un `tmp_path` sin tocar el código de producción:

```python
# tests/conftest.py
@pytest.fixture
def app(tmp_path, monkeypatch):
    db = str(tmp_path / "test_settings.db")
    monkeypatch.setattr("app.services.settings_service._DB_PATH", db)
    ...
```

Si `_DB_PATH` fuera una constante calculada eagerly al import time, esto no funcionaría: el servicio ya habría resuelto la ruta antes de que monkeypatch pudiera intervenir.

### `_resolve_db_path()` separado de `_get_db_path()`

- `_resolve_db_path()` — pura función de platform → path. Fácil de testear.
- `_get_db_path()` — cachea la resolución, usa el global si está seteado. Es el único punto que lee `_DB_PATH`.

### Conexión fresca por operación

```python
with _conn() as c:
    c.execute(...)
```

El `with` se encarga del commit (y rollback si excepción). No hay estado global de conexión. Esto **sacrifica** reuso de conexión pero **elimina** bugs de threading en Flask + SQLite (los threads no pueden compartir conexiones SQLite).

### `_init_db()` idempotente

- `CREATE TABLE IF NOT EXISTS` — seguro re-ejecutar.
- Nuevas columnas con `_ensure_column()` helper — re-ejecutar solo añade lo que falta.

**No usar Alembic**. Con esto cada arranque auto-migra sin boilerplate.

### `PRAGMA journal_mode=WAL`

Permite lecturas concurrentes con una escritura. Esencial si la app puede abrir web + desktop simultáneos apuntando al mismo `settings.db`.

### JSON-encoded values

Para settings que son estructuras (listas, dicts), serializamos a JSON. Evita añadir columnas por cada nuevo setting — el schema se mantiene como KV store genérico.

## Variantes

### Secretos (passwords)

Nunca JSON-encodear passwords. Usa `werkzeug.security.generate_password_hash`:

```python
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username: str, password: str, role: str = "user") -> None:
    pwhash = generate_password_hash(password)
    with _conn() as c:
        c.execute(
            "INSERT INTO users (username, pwhash, role) VALUES (?, ?, ?)",
            (username, pwhash, role),
        )


def authenticate(username: str, password: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT username, pwhash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not row or not check_password_hash(row["pwhash"], password):
        return None
    return {"username": row["username"], "role": row["role"]}
```

### DB remota (MariaDB/PostgreSQL)

Mismo patrón pero `_conn()` vive en un servicio separado (`db.py`), y la configuración (host, port, user, password) se lee desde `settings.db` para ser editable sin reiniciar:

```python
# app/services/db.py
import mysql.connector
from app.services import settings_service


def get_conn():
    cfg = settings_service.get_setting("db_config", {})
    return mysql.connector.connect(
        host=cfg.get("host"),
        port=cfg.get("port", 3306),
        user=cfg.get("user"),
        password=cfg.get("password"),
        database=cfg.get("database"),
    )
```

## Errores típicos

- **Resolver `_DB_PATH` eagerly al import**: rompe los tests. Usa lazy.
- **Compartir conexión entre threads**: SQLite lo bloquea. Conexión nueva por operación.
- **Olvidar `ON CONFLICT DO UPDATE`** en upserts: usa siempre que la key sea primary.
- **No poner WAL mode**: lecturas concurrentes se bloquean.
