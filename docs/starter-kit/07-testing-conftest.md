# 07 · Testing — conftest + fixtures

Patrón de testing: pytest + SQLite real en `tmp_path` (no mocks) + fixtures que monkeypatch todos los `_DB_PATH` de servicios al mismo path temporal.

## Setup

```bash
pip install pytest
```

Añade a `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

## Estructura

```
tests/
├── conftest.py             # Fixtures compartidas
├── unit/                   # Tests de servicios aislados
│   ├── test_settings_service.py
│   ├── test_auth_service.py
│   └── ...
└── integration/            # Tests de routes (HTTP-level)
    ├── test_routes_auth.py
    ├── test_routes_api.py
    └── ...
```

**Naming**: `test_<archivo_que_testea>.py`. Un archivo del código → un archivo de tests.

## `tests/conftest.py`

```python
import os
import pytest
from app import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Fresh Flask app per test with isolated SQLite DBs in tmp_path."""
    db_path = str(tmp_path / "test_settings.db")
    auth_db_path = str(tmp_path / "test_auth.db")

    # Monkeypatch all _DB_PATH globals before create_app runs init_db()
    monkeypatch.setattr("app.services.settings_service._DB_PATH", db_path)
    monkeypatch.setattr("app.services.auth_service._DB_PATH", auth_db_path)
    # Add one line per service that has its own _DB_PATH

    # If you have in-memory caches, invalidate here to prevent leakage
    # from app.services.keys_cache import keys_cache
    # keys_cache.invalidate()

    application = create_app()
    application.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DEV_MODE": True,          # auto-login as admin for convenience
    })
    yield application


@pytest.fixture()
def client(app):
    """Flask test client with DEV_MODE auto-login."""
    return app.test_client()


@pytest.fixture()
def admin_session(client):
    """Forced admin identity, overrides dev auto-login."""
    with client.session_transaction() as sess:
        sess["user_id"]  = "admin"
        sess["is_admin"] = True
        sess["is_guest"] = False
        sess["role"]     = "admin"
    return client


@pytest.fixture()
def guest_session(client):
    """Guest identity for testing 403s."""
    with client.session_transaction() as sess:
        sess["user_id"]  = "guest"
        sess["is_admin"] = False
        sess["is_guest"] = True
        sess["role"]     = "user"
    return client


@pytest.fixture()
def user_session(client):
    """Non-admin non-guest user."""
    with client.session_transaction() as sess:
        sess["user_id"]  = "alice"
        sess["is_admin"] = False
        sess["is_guest"] = False
        sess["role"]     = "user"
    return client
```

## Por qué este patrón

### SQLite real, no mocks

```python
monkeypatch.setattr("app.services.settings_service._DB_PATH", db_path)
```

Los servicios se ejecutan contra un SQLite **real** en `tmp_path`. Ventajas sobre mocks:

- Los tests **prueban el SQL real**, no una interfaz inventada.
- Schema bugs (columna que falta, constraint violado) se cazan.
- Zero boilerplate de mock setup.
- Veloces igualmente (SQLite en tmpfs es <1ms por operación).

La única cosa que mockeamos es MariaDB remota — porque a) necesita red, b) no puedes asumir que un dev tiene una MariaDB corriendo, c) los tests deberían poder correr offline.

### Monkeypatch antes de `create_app()`

Orden crítico:

```python
monkeypatch.setattr("app.services.X._DB_PATH", tmp_db)   # 1. First
application = create_app()                               # 2. Then
```

`create_app()` llama `init_db()` en cada servicio. Si el monkeypatch corre **después**, el servicio ya tiene cacheada la ruta real.

### Fresh app per test

`yield application` con la fixture `app` **sin scope** (default = function) → cada test obtiene una instancia nueva, con DBs nuevas. Sin cross-contamination entre tests.

Coste: ~20ms por test (crear app + init_db). Aceptable para suites de miles de tests.

### Fixtures de sesión explícitas

```python
admin_session, guest_session, user_session
```

En vez de hacer `client.session_transaction()` a mano en cada test, centralizamos los escenarios típicos.

## Tests de ejemplo

### Unit — servicio directo

```python
# tests/unit/test_settings_service.py
from app.services import settings_service


def test_set_and_get_setting(app):
    settings_service.set_setting("theme", "dark")
    assert settings_service.get_setting("theme") == "dark"


def test_get_missing_setting_returns_default(app):
    assert settings_service.get_setting("nonexistent", "fallback") == "fallback"


def test_setting_value_survives_process(app):
    settings_service.set_setting("list_pref", [1, 2, 3])
    # JSON-serialized roundtrip
    assert settings_service.get_setting("list_pref") == [1, 2, 3]
```

La fixture `app` se usa solo por side-effect (el monkeypatch del `_DB_PATH`), pero el servicio se llama directamente. Patrón común en unit tests.

### Integration — route HTTP

```python
# tests/integration/test_routes_auth.py
def test_login_page_renders(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Username" in resp.data


def test_login_success_redirects(client, app):
    from app.services import auth_service
    auth_service.create_user("alice", "secret123")

    resp = client.post("/login", data={"username": "alice", "password": "secret123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")


def test_admin_endpoint_rejects_guest(guest_session):
    resp = guest_session.post("/admin/users/alice/delete")
    assert resp.status_code == 403


def test_admin_endpoint_allows_admin(admin_session, app):
    from app.services import auth_service
    auth_service.create_user("bob", "pw")

    resp = admin_session.post("/admin/users/bob/delete")
    assert resp.status_code in (200, 302)
    assert auth_service.get_user("bob") is None
```

## Comandos útiles

```bash
python -m pytest tests/                         # Todo
python -m pytest tests/unit/                    # Solo unit
python -m pytest tests/integration/             # Solo integration
python -m pytest tests/ -k "login"              # Match por nombre
python -m pytest tests/unit/test_auth.py -v     # Un archivo con verbose
python -m pytest -x                             # Stop en primer fallo
python -m pytest --lf                           # Solo los que fallaron el último run
python -m pytest -n auto                        # Paralelo (pip install pytest-xdist)
```

## Política

Regla operativa: **cada cambio de código lleva tests**. Unit para lógica de servicios, integration para routes. Cambios puramente visuales (CSS, template markup sin lógica nueva) son excepción.

No hay umbral de coverage — pero "no tests, no merge" sí.

## Coverage (opcional)

```bash
pip install coverage
coverage run -m pytest tests/
coverage report --include="app/*"
coverage html      # genera htmlcov/index.html
```

Informal, no es un gate.

## CI (opcional)

Por defecto NO corre en CI (ver [ADR-0009](../adr/0009-no-ci-tests.md)). Si lo quieres:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with: {python-version: '3.11'}
      - run: pip install -e ".[dev]"
      - run: python -m pytest
```
