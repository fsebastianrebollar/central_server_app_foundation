# 06 · Flask-Babel i18n

Multi-idioma con gettext: strings en Python y Jinja via `_(...)`, strings en JS inyectadas desde el backend.

## Setup inicial

### Dependencia

```bash
pip install flask-babel
```

Añade a `pyproject.toml`:

```toml
dependencies = [
    # ...
    "flask-babel>=4.0",
]
```

### Configuración en `create_app()`

```python
from flask import Flask, session, request, has_request_context
from flask_babel import Babel

SUPPORTED_LANGS = ("en", "es", "de")


def get_locale():
    if not has_request_context():
        return "en"                                      # 1. Tests, bg jobs
    lang = session.get("lang", "") or request.cookies.get("lang", "")
    if lang in SUPPORTED_LANGS:
        return lang                                      # 2. Explicit user choice
    return request.accept_languages.best_match(
        list(SUPPORTED_LANGS), default="en"
    )                                                    # 3. Browser Accept-Language


def create_app():
    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

    babel = Babel(app, locale_selector=get_locale)

    @app.context_processor
    def inject_lang():
        return {"current_lang": get_locale()}

    # ... rest of factory
```

**Nota crítica**: el `has_request_context()` guard hace que servicios que usan `gettext` fuera de request (scheduled jobs, startup) no exploten. Sin él, cualquier `_("error msg")` en un service lanzado desde `atexit` o un thread bg revienta.

## Estructura de archivos

```
app/
├── __init__.py
└── translations/
    ├── babel.cfg                       # extract config
    ├── messages.pot                    # template POT (auto-generated)
    ├── en/LC_MESSAGES/messages.po      # English (base)
    ├── es/LC_MESSAGES/messages.po      # Spanish
    └── de/LC_MESSAGES/messages.po      # German
```

### `babel.cfg`

```
[python: app/**.py]
[jinja2: app/templates/**.html]
```

Cubre todo el Python y Jinja. JS no se extrae automáticamente (ver § JS strings).

## Flujo de trabajo

### Extraer strings

```bash
pybabel extract -F app/translations/babel.cfg -o app/translations/messages.pot .
```

### Crear idioma nuevo

```bash
pybabel init -i app/translations/messages.pot -d app/translations -l fr
```

Crea `app/translations/fr/LC_MESSAGES/messages.po` vacío.

### Actualizar tras añadir strings

```bash
pybabel update -i app/translations/messages.pot -d app/translations
```

Merge los nuevos msgids manteniendo traducciones existentes. Los nuevos quedan con `msgstr ""`.

### Compilar

```bash
pybabel compile -d app/translations
```

Genera `.mo` por idioma. **Los `.mo` son los que Flask-Babel lee en runtime**.

**Importante**: commitear `.po` Y `.mo`. No hay step de compilación en CI — si olvidas el `.mo`, el idioma no se aplica en el binario.

## Uso

### Python

```python
from flask_babel import gettext as _

raise ValueError(_("Username already exists"))
```

### Jinja

```jinja
<h1>{{ _("Welcome") }}</h1>
<p>{{ _("Hello %(name)s", name=current_user) }}</p>
```

### JavaScript — dos patrones

JS no puede extraerse con pybabel (no soporta sintaxis JS). Soluciones:

#### Patrón A: dict global `_t` via template

En `__init__.py`, genera un dict con todas las strings compartidas:

```python
def _js_translations():
    from flask_babel import gettext as _
    return {
        "save":            _("Save"),
        "cancel":          _("Cancel"),
        "confirm_delete":  _("Are you sure?"),
        # ...
    }


@app.context_processor
def inject_js_translations():
    return {"js_translations": _js_translations()}
```

En `base.html`:

```jinja
<script>
    const _t = {{ js_translations | tojson }};
</script>
```

En JS:

```javascript
document.querySelector("#save-btn").textContent = _t.save;
confirm(_t.confirm_delete);
```

#### Patrón B: `const T` local por template

Para strings específicas de una página:

```jinja
<script>
    const T = {
        page_title:   "{{ _('Report Configuration') }}",
        loading_hint: {{ _('Loading...') | tojson }},
        complex_msg:  {{ _('Click "Refresh" to reload') | tojson }},
    };
</script>
```

### ⚠️ Trampa: comillas en strings JS

**Este patrón rompe**:

```jinja
bad: "{{ _('Click \"Refresh\" button') }}",
```

Jinja renderiza los `\"` como comillas literales, y el JS queda:

```js
bad: "Click "Refresh" button",   // SyntaxError — kills entire <script>
```

El SyntaxError tumba todos los handlers del `<script>` afectado.

**Fix**: `| tojson`:

```jinja
good: {{ _('Click "Refresh" button') | tojson }},
```

`| tojson` emite un JSON string con todo escapado correctamente.

### ⚠️ Trampa: `%(name)s` vs `{name}`

Jinja i18n hace `%`-formatting automático. Si tu string tiene un placeholder:

- `%(name)s` → Jinja intenta formatear; si no pasas `name=...` junto a `gettext`, lanza `KeyError`.
- `{name}` → OK; formateo manual en JS con `_t.msg.replace('{name}', value)` o template literal.

**Regla**: en strings destinadas a JS (dict compartido), usa siempre `{name}`.

## Selector de idioma

Endpoint `/lang/<lang>`:

```python
@auth_bp.get("/lang/<lang>")
def set_language(lang):
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    session["lang"] = lang
    if session.get("user_id") and not session.get("is_guest"):
        # Persist per-user
        settings_service.set_user_pref(session["user_id"], "lang", lang)
    resp = redirect(request.referrer or "/")
    resp.set_cookie("lang", lang, max_age=60*60*24*365, samesite="Lax")
    return resp
```

UI: un dropdown en el header con los idiomas soportados.

## Qué NO traducir

- **Identificadores técnicos** (nombres de columna DB, claves de settings, tags): en inglés siempre.
- **Logs** (`logger.info(...)`): inglés.
- **Commits / branches / PRs**: inglés.
- **Valores de dominio** que luego se matchean con regex en código.

## Flujo de añadir un string nuevo

1. En template: `{{ _("My new text") }}`.
2. En Python: `from flask_babel import gettext as _; _("My new text")`.
3. En JS compartido: añade al dict en `_js_translations()`.
4. En JS local: añade al `const T = {...}` del template.
5. `pybabel extract && pybabel update && <edita .po files> && pybabel compile`.
6. Commit: `.pot` + todos los `.po` + todos los `.mo`.

Si olvidas compilar, la app usa el msgid original como fallback — el idioma "parece" roto pero no revienta.
