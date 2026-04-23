# 10 · Contexto para Claude Code en apps consumer

Fragmento listo para pegar en el `CLAUDE.md` de una app que usa
`central_server_app_foundation` como chassis. Cópialo tal cual y rellena los
`<PLACEHOLDER>` con los valores de tu proyecto.

---

```markdown
## Chassis: central_server_app_foundation

Esta app usa `central_server_app_foundation` como librería chassis. Antes de
implementar cualquier feature de infraestructura (auth, settings, diseño, i18n,
health endpoint) comprueba si el chassis ya lo resuelve.

Referencia completa de la API:
https://github.com/fsebastianrebollar/central_server_app_foundation/blob/main/CLAUDE.md

---

### Qué da el chassis (no reimplementes esto)

| Necesidad | Módulo chassis | Cómo se activa |
|---|---|---|
| Login / logout / roles / admin CRUD | `auth_ui` | `create_auth_blueprint()` |
| Página de perfil de usuario | `auth_ui` | incluida en el blueprint |
| Sidebar + base template + tema | `design` | `create_design_blueprint()` |
| CSS del sistema de diseño | `design` | cargado automáticamente por `base.html` |
| CSS de botones settings / formularios modal | `settings_ui` | cargado automáticamente por `base.html` |
| Secciones de la página /settings | `settings_ui` | `create_settings_blueprint()` |
| Preferencias de usuario y settings globales | `settings` | `SettingsStore` |
| Endpoint /health, /version, /icon | `contract` | `create_health_blueprint()` |
| Flags CLI del contrato supervisor | `contract` | `build_parser()` |
| i18n (Babel, locale resolver) | `i18n` | `init_babel()` + `make_locale_resolver()` |

### Lo que la app sí debe implementar

- **Context processor** con `current_user`, `is_admin`, `is_guest`, `current_lang`,
  `user_theme` — el chassis los consume pero no los inyecta. Ver ejemplo en
  `template_app/app.py`.
- **Rutas de dominio** — toda la lógica de negocio vive en blueprints propios.
- **Ruta `/settings`** — el chassis provee el shell (`_sections.html`) pero la
  app registra el endpoint y pasa el contexto de dominio a los modales.
- **Templates de dominio** — extienden `central_server_app_foundation/design/base.html`.

---

### Clases CSS disponibles del chassis

Usa estas clases directamente en templates. No las redefinas en el CSS de la app.

**Layout / contenido**
`card`, `card-section`, `card-section-last`, `card-title-row`, `text-secondary`,
`section-label`, `table-wrap`, `clickable-row`, `row-ok`, `row-fail`, `mono`

**Botones**
`login-btn`, `btn-back`, `btn-narrow`, `btn-danger`, `btn-logout`

**Badges**
`badge`, `badge-ok`, `badge-fail`, `badge-other`,
`admin-badge`, `admin-badge-operator`, `admin-badge-supervisor`, `admin-badge-admin`,
`admin-badge-sm`, `guest-badge-sm`

**Settings / formularios modal**
`settings-buttons`, `settings-btn`, `settings-btn-icon`,
`db-form`, `db-form-row`, `db-label`,
`db-status`, `db-status-ok`, `db-status-error`,
`setup-input`, `cache-size-options`, `cache-size-option`, `cache-size-label`

**Modales**
`modal-overlay`, `modal-open`, `modal-box`, `modal-header`, `modal-body`,
`modal-footer`, `modal-close`, `modal-label`, `modal-input`, `modal-error`,
`modal-hint`

**Admin / usuario**
`admin-user-list`, `admin-user-row`, `admin-user-name`, `admin-user-actions`,
`admin-btn`, `admin-btn-change`, `admin-btn-delete`

**Flash**
`flash`, `flash-success`, `flash-error`

---

### Trampas conocidas

**1. Endpoint del sidebar — usa la ruta que renderiza, no un redirect.**
El chassis marca el tab activo comparando `request.endpoint` con el endpoint
declarado en la entrada del sidebar. Si el entry apunta a una ruta que hace
`redirect()`, el tab nunca se ilumina porque el browser llega al endpoint
destino, no al origen.

```python
# MAL — /index redirige a /dashboard; el tab nunca queda activo
sidebar.entry("Dashboard", endpoint="main.index")

# BIEN — apunta directamente a la ruta que renderiza la página
sidebar.entry("Dashboard", endpoint="main.dashboard")
```

**2. La ruta `/settings` la crea la app, no el chassis.**
El chassis registra el *shell* (las secciones con botones) y sirve su CSS, pero
el endpoint `/settings` con toda su lógica de dominio es responsabilidad de la app.
Las secciones visibles se inyectan automáticamente en el contexto como
`chassis_settings_sections` — el template solo hace `{% include "_sections.html" %}`.

**3. Los modales de settings viven en el template de la app.**
El chassis renderiza los botones de cada sección pero los modales que abren
son DOM de la app. El `onclick` del botón llama a una función JS que la app define.

**4. La página `/user` la sirve el chassis, pero sus modales usan clases del chassis.**
Los formularios de cambio de contraseña, creación de usuario, etc. usan
`.db-form`, `.db-form-row`, `.db-label`, `.db-status` — clases de `settings.css`.
Este CSS se carga automáticamente cuando el settings blueprint está registrado.
Si los botones de `/user` se ven sin estilo, confirma que `create_settings_blueprint()`
está registrado en `create_app()`.

---

### Checklist de integración mínima

- [ ] `pip install "central-server-app-foundation @ git+https://..."`
- [ ] `_user_store = UserStore(db_path=lambda: ..., admin_user=..., admin_pass=...)`
- [ ] `_settings_store = SettingsStore(db_path=lambda: ...)`
- [ ] En `create_app()`: `_user_store.init_schema()` + `_settings_store.init_schema()`
- [ ] Context processor inyecta `current_user`, `is_admin`, `is_guest`, `current_lang`, `user_theme`
- [ ] `app.register_blueprint(create_auth_blueprint(...))`
- [ ] `app.register_blueprint(create_design_blueprint(...))`
- [ ] `app.register_blueprint(create_settings_blueprint(...))`
- [ ] `app.register_blueprint(create_health_blueprint(...))`
- [ ] Templates de dominio extienden `central_server_app_foundation/design/base.html`
- [ ] Sidebar entries apuntan a endpoints que renderizan (no redirects)
- [ ] La app tiene su propia ruta `/settings` que renderiza con `{% include "_sections.html" %}`

El archivo `template_app/app.py` en el repo del chassis es la implementación de
referencia de todo lo anterior.
```
