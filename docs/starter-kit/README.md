# Starter Kit — central_server_app_foundation

Plantillas y snippets **copiables** para bootstrapear un proyecto nuevo usando el chassis: Flask 3 + `central_server_app_foundation` + SQLite local + DB remota opcional + desktop PyInstaller + semantic-release con gate `/compile` + i18n Flask-Babel.

Este directorio NO es código ejecutable — son fragmentos de referencia. El flujo es: lees la checklist de bootstrap, copias los snippets relevantes al nuevo repo, adaptas nombres. Los snippets ya asumen que `central_server_app_foundation` está instalado como dependencia pip.

## Índice

1. [Checklist de bootstrap](00-checklist.md) — orden recomendado para arrancar un repo desde cero.
2. [Flask factory](01-flask-factory.md) — `create_app()`, blueprints, before_request.
3. [Patrón de servicio SQLite](02-sqlite-service.md) — `_DB_PATH` monkeypatcheable, `_init_db()` auto-migrate.
4. [Dual runtime (web + desktop)](03-dual-runtime.md) — `run.py` con argparse, pywebview, sys.frozen.
5. [PyInstaller spec](04-pyinstaller-spec.md) — `conter_stats.spec` multiplataforma, hiddenimports, datas.
6. [GitHub Actions: release + build](05-github-actions.md) — `release.yml` + `build.yml` + gate `/compile`.
7. [Flask-Babel i18n](06-i18n-babel.md) — `babel.cfg`, extraer/compilar, patrón JS con `| tojson`.
8. [Testing: conftest + fixtures](07-testing-conftest.md) — `app`, `client`, `admin_session`, monkeypatch DBs.
9. [Auth con admin bootstrap](08-auth-bootstrap.md) — roles, guest, admin hardcoded inicial.
10. [Cache in-process pattern](09-cache-pattern.md) — pickle on-disk + RAM LRU + invariantes.

## Filosofía

El chassis te da la estructura; el starter-kit te da los snippets. No copies `central_server_app_foundation` entero — instálalo como dependencia y usa solo lo que necesitas.

1. Arranca el nuevo repo con `mkdir + git init`.
2. Instala: `pip install "central-server-app-foundation @ git+https://github.com/fsebastianrebollar/central_server_app_foundation.git"`
3. Sigue la **checklist** de bootstrap.
4. En cada paso, abre el snippet correspondiente aquí y **cópialo + adapta**.
5. Al terminar, el nuevo proyecto es autónomo — el chassis lo consumes como librería, no como herencia de código.

## Qué NO está aquí

- **Lógica de dominio** (filtros de tests, charts de fábrica, etc.) — eso es específico de conter-stats.
- **Schema de MariaDB** — el tuyo será otro.
- **Design language** — eso es [`../design_language/`](../design_language/README.md); está en este mismo repo, replicable pero más subjetivo.
- **Dependencias opcionales** (reports scheduler, Gantt, Logic view) — añádelas si el proyecto nuevo las necesita, no por inercia.

## Qué va aquí vs. qué va en ADR

- **ADR** explica *por qué* tomamos una decisión. Útil para juzgar si esa decisión aplica a tu proyecto nuevo.
- **Starter-kit** te da el *cómo* — código listo para copiar.

Antes de copiar un snippet, lee el ADR asociado para ver si la decisión original encaja con tu contexto. Los patterns del starter-kit son opiniones, no verdades.

Los ADRs que justifican cada decisión viven en `conter-stats/docs/adr/` (el proyecto de referencia). Consulta ese repo para el razonamiento original.

| Snippet | ADR en conter-stats |
|---|---|
| 01-flask-factory | adr/0001-flask-no-fastapi.md |
| 02-sqlite-service | adr/0003-sqlite-local-mariadb-remote.md |
| 03-dual-runtime | adr/0004-pyinstaller-no-electron.md |
| 04-pyinstaller-spec | adr/0004-pyinstaller-no-electron.md |
| 05-github-actions | adr/0007-semantic-release-compile-gate.md |
| 06-i18n-babel | — |
| 07-testing-conftest | adr/0009-no-ci-tests.md |
| 08-auth-bootstrap | adr/0006-flask-session-no-jwt.md |
| 09-cache-pattern | adr/0008-in-process-caches-no-redis.md |
