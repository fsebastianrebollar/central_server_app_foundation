# 00 · Checklist de bootstrap

Orden recomendado para arrancar un repo nuevo. Cada paso linka al snippet correspondiente.

## Día 0 — repo y entorno

- [ ] `mkdir my-app && cd my-app && git init`
- [ ] Crear `pyproject.toml` mínimo ([ver snippet](05-github-actions.md#pyprojecttoml)):
  ```toml
  [project]
  name = "my-app"
  version = "0.1.0"
  requires-python = ">=3.10"
  dependencies = ["flask>=3.0"]
  ```
- [ ] `python -m venv .venv && source .venv/bin/activate`
- [ ] `pip install -e .`
- [ ] `.gitignore` incluye `.venv/`, `__pycache__/`, `dist/`, `build/`, `*.db`, `cache/`, `.DS_Store`.
- [ ] Primer commit: `git commit -m "chore: initialize project"` (no bumpea versión).

## Día 1 — skeleton Flask

- [ ] Estructura base:
  ```
  app/
  ├── __init__.py
  ├── routes/
  │   ├── __init__.py
  │   └── main.py
  ├── services/
  │   └── __init__.py
  ├── templates/
  │   └── base.html
  └── static/
      ├── css/style.css
      └── js/app.js
  ```
- [ ] Copia [`01-flask-factory.md`](01-flask-factory.md) y adapta.
- [ ] Un endpoint dummy (`/` → "hello").
- [ ] `python -m flask --app app run` debería levantar.

## Día 1 — dual runtime

- [ ] Copia `run.py` de [`03-dual-runtime.md`](03-dual-runtime.md).
- [ ] `pip install pywebview` (opcional, si quieres modo desktop).
- [ ] Verifica: `python run.py` (web) y `python run.py --desktop` (ventana).

## Día 2 — primer servicio SQLite

- [ ] Copia el patrón de [`02-sqlite-service.md`](02-sqlite-service.md) para un servicio simple (ej: `settings_service.py`).
- [ ] `_DB_PATH` vive en `~/Library/Application Support/MyApp/` (macOS) o `%APPDATA%\MyApp\` (Windows).
- [ ] `_init_db()` crea las tablas si no existen — auto-migrate.

## Día 2 — tests

- [ ] `pip install pytest`
- [ ] Copia `conftest.py` de [`07-testing-conftest.md`](07-testing-conftest.md).
- [ ] `tests/unit/test_settings_service.py` — un test básico que valida `_DB_PATH` monkeypatched.
- [ ] `python -m pytest` debe pasar.

## Día 3 — autenticación

- [ ] Copia [`08-auth-bootstrap.md`](08-auth-bootstrap.md): `auth_service.py` + endpoints en `routes/auth.py`.
- [ ] Cambia el admin hardcoded (`_ADMIN_USER`, `_ADMIN_PASS`) a algo propio.
- [ ] Añade `@before_request` al factory para gate de auth (excepto `PUBLIC_ENDPOINTS`).
- [ ] Dev mode: auto-login como admin si `not sys.frozen`.

## Día 4 — CI / release

- [ ] Crea `.github/workflows/release.yml` copiando de [`05-github-actions.md`](05-github-actions.md).
- [ ] Crea `.github/workflows/build.yml` (condicional al `/compile`).
- [ ] Actualiza `pyproject.toml` con la sección `[tool.semantic_release]`.
- [ ] Primer commit con `feat:` → confirma que el workflow bumpea versión.
- [ ] Primer commit con `feat: ... /compile` → confirma que compila.

## Día 5 — PyInstaller

- [ ] Copia `my_app.spec` de [`04-pyinstaller-spec.md`](04-pyinstaller-spec.md).
- [ ] Ajusta `datas=[...]` a tus paths.
- [ ] `pip install -e ".[build]"` (pyinstaller como extra).
- [ ] `pyinstaller my_app.spec` — verifica que el `.app`/`.exe` abre y funciona.
- [ ] Si rompe por `ModuleNotFoundError`: añade al `hiddenimports`.

## Día 6 — i18n (opcional)

- [ ] Si el proyecto es multi-idioma, copia [`06-i18n-babel.md`](06-i18n-babel.md).
- [ ] `pip install flask-babel`.
- [ ] `app/translations/babel.cfg` + `get_locale()` + `SUPPORTED_LANGS`.
- [ ] Primer string `_("Hello")` en un template, extrae y compila.

## Día 7 — caches (opcional)

- [ ] Solo si tienes queries caras repetibles. Si no, sáltatelo.
- [ ] Copia [`09-cache-pattern.md`](09-cache-pattern.md).
- [ ] Recuerda: **cada clave incluye filtros + discriminadores de tenant/producto/lo-que-sea**. Nunca solo `(keys, columns)`.

## Checks finales antes del primer release público

- [ ] `python -m pytest` verde.
- [ ] `python run.py` arranca.
- [ ] `python run.py --desktop` abre ventana.
- [ ] `pyinstaller my_app.spec` produce binario válido.
- [ ] `feat: ...` + `/compile` pushea, compila, sube assets al Release.
- [ ] `README.md` del repo explica: qué es, cómo arrancar en dev, cómo instalar el binario.
- [ ] `CLAUDE.md` con arquitectura actual (si vas a trabajar con Claude Code).
- [ ] Copiar `docs/adr/` y `docs/dev_guide/` relevantes al nuevo repo.
