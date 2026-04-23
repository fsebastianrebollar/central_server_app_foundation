# 07 · Formularios

Patrón común: **todos los controles son monospace, fondo `--input-bg`, borde 1px `--border`, al foco el borde pasa a `--neon` y aparece un halo suave con `--neon-subtle` o `--neon-glow`**. No hay sans-serif, no hay gradientes, no hay bordes redondeados > 10px.

## 7.1 · Text inputs

```css
.setup-input,
.fbar-input,
.ws-modal-input {
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;              /* 13px en inputs densos (filter bar) */
    background-color: var(--input-bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    outline: none;
    font-family: inherit;         /* hereda monospace */
    transition: border-color 0.15s;
}

.setup-input:focus,
.ws-modal-input:focus {
    border-color: var(--neon);
}
```

### Variantes

| Clase | Uso | Padding | Font-size |
|---|---|---|---|
| `.setup-input` | Formulario de first-run, login, settings | `10px 12px` | `14px` |
| `.ws-modal-input` | Nombre/descripción en modal de workspace | `10px 12px` | `14px` |
| `.fbar-input` | Input del filter bar (condición) | `6px 10px` | `13px` |
| `.fbar-date` | Input `type="date"` del filter bar | `6px 10px` | `13px`, focus azul (`--neon-blue`) |

### Regla

- **Ancho**: `width: 100%` y el padre define el max-width. No fijar width absoluto.
- **Border-radius**: siempre `6px` (inputs densos `4px`).
- **Placeholder**: usa `color: var(--text-secondary); opacity: 1;` — evita placeholders borrosos.
- **Disabled**: `cursor: not-allowed; opacity: 0.5;`.

## 7.2 · Select (custom dropdown con chevron SVG)

```css
select {
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-color: var(--input-bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 32px 8px 12px;      /* espacio derecho para el chevron */
    font-size: 13px;
    font-family: inherit;
    line-height: 1.25;
    cursor: pointer;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s, background-color 0.15s;

    /* Chevron neutro en gris (default) */
    background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%239ca3af' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    background-size: 10px 7px;
}

select:hover { border-color: var(--text-secondary); }

select:focus {
    border-color: var(--neon);
    box-shadow: 0 0 0 3px var(--neon-subtle);
    /* Chevron naranja al foco */
    background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%23ff6a00' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}

select option {
    background: var(--bg-surface);
    color: var(--text);
}
```

- **No uses el chevron nativo**: `appearance: none` + SVG inline. Evitamos que Windows/Linux rompan el look.
- **Chevron gris → naranja al foco**: el cambio de color del trazo es una micro-señal deliberada.
- **No intentes estilar `<option>` más allá de fondo/color**: los navegadores ignoran casi todo. Si necesitas un dropdown rico, construye un popover custom (ver `.pd-dropdown` en `components`).

## 7.3 · Textarea

```css
.ws-modal-textarea {
    min-height: 80px;
    resize: vertical;
    /* hereda el resto de .ws-modal-input */
}
```

Reglas:
- **`resize: vertical`** siempre; nunca `resize: both` (rompe el layout del modal).
- **`min-height: 80px`**, sin `max-height` — deja que el usuario expanda.
- Hereda padding, font, border y focus del input estándar. No redefinas el focus.

## 7.4 · Checkbox switch

Firma visual: **pill horizontal con dot que se desliza y se enciende en neón**. No es un cuadrado con tick — es un toggle.

```css
input[type="checkbox"] {
    -webkit-appearance: none;
    appearance: none;
    width: 30px;
    height: 16px;
    border-radius: 10px;
    border: 1.5px solid var(--border);
    background: var(--input-bg);
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

input[type="checkbox"]::before {
    content: '';
    position: absolute;
    top: 50%; left: 2px;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--text-secondary);
    opacity: 0.65;
    transform: translateY(-50%);
    transition: left 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, opacity 0.18s ease;
}

input[type="checkbox"]:hover { border-color: var(--neon); }
input[type="checkbox"]:hover::before { opacity: 1; }

input[type="checkbox"]:checked {
    border-color: var(--neon);
    background: linear-gradient(135deg, rgba(255, 106, 0, 0.18), rgba(255, 140, 51, 0.08));
    box-shadow: 0 0 8px rgba(255, 106, 0, 0.28);
}

input[type="checkbox"]:checked::before {
    left: calc(100% - 12px);       /* slide a la derecha */
    background: var(--neon);
    opacity: 1;
    box-shadow: 0 0 6px var(--neon), 0 0 10px rgba(255, 106, 0, 0.55);
}

input[type="checkbox"]:focus-visible {
    outline: 2px solid rgba(255, 106, 0, 0.4);
    outline-offset: 2px;
}

input[type="checkbox"]:disabled {
    cursor: not-allowed;
    opacity: 0.45;
}
```

### Notas

- **Es global**: aplica a `input[type="checkbox"]` sin clase. No re-estilizar por componente — rompes la firma.
- **No hay tick visible**: el estado se lee por color + posición del dot. Perfecto semántica on/off; **NO lo uses** para opciones de selección múltiple en una lista larga — ahí podría resultar confuso y ambiguo. (Caso actual: settings, filter presets, workspace visibility toggle.)
- **`flex-shrink: 0`**: obligatorio cuando el checkbox está dentro de un flex row con label — si no, el label lo aplasta.

## 7.5 · Radio neón

Círculo pequeño con dot neón al seleccionar. Mismo principio que el checkbox pero en forma circular.

```css
input[type="radio"] {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1.5px solid var(--border);
    background: var(--input-bg);
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

input[type="radio"]::before {
    content: '';
    position: absolute;
    inset: 3px;
    border-radius: 50%;
    background: var(--neon);
    opacity: 0;
    transform: scale(0.4);
    transition: opacity 0.18s, transform 0.18s, box-shadow 0.18s;
}

input[type="radio"]:hover { border-color: var(--neon); }

input[type="radio"]:checked {
    border-color: var(--neon);
    box-shadow: 0 0 8px rgba(255, 106, 0, 0.35);
}

input[type="radio"]:checked::before {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 6px var(--neon), 0 0 10px rgba(255, 106, 0, 0.5);
}

input[type="radio"]:focus-visible {
    outline: 2px solid rgba(255, 106, 0, 0.4);
    outline-offset: 2px;
}
```

## 7.6 · Labels

No hay una clase canónica para labels. Patrones por contexto:

### Label horizontal junto al control

```html
<label style="display: flex; align-items: center; gap: 8px;">
    <input type="checkbox" ...>
    <span>Mostrar filas vacías</span>
</label>
```

No fijar font-size explícito — hereda los `13px` del body.

### Label en bloque sobre el control (forms de settings)

Usa `.section-label`:

```css
.section-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}
```

### Label dentro de un modal (ws-modal, reports modal)

Clases scoped — cada modal tiene su propio label, pero todas siguen el patrón "uppercase + letter-spacing". Ver `style.css` > `.ws-modal-label`, `.reports-modal-label`, etc.

## 7.7 · Grupos de campos

Patrón `.admin-form-column` para stacked vertical:

```css
.admin-form-column {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.admin-form-row {
    display: flex;
    gap: 8px;
    align-items: center;
}
```

No introducir `<fieldset>`/`<legend>` — no los estilizamos y se ven mal por defecto.

## 7.8 · Validación y errores

No hay sistema CSS de validación propio (no `.is-invalid` ni `:invalid {}`). Los errores se manejan a través de:

1. **Flash messages** al topar: `.flash-error` (ver `06-components`).
2. **Flash toasts** emitidos por JS en formularios AJAX (`.flash-toast-error`).
3. En algunos modales, un banner `<div class="modal-error">` inline — no es un patrón global.

**Regla**: **NO** cambies el borde del input a rojo sin también mostrar un mensaje. Un input rojo sin contexto es hostil.

## 7.9 · Ejemplo completo: formulario de nuevo usuario

```html
<form class="admin-form-column">
    <div class="admin-form-column">
        <span class="section-label">Nombre de usuario</span>
        <input type="text" class="setup-input" name="username" required>
    </div>

    <div class="admin-form-column">
        <span class="section-label">Rol</span>
        <select name="role" class="setup-input">
            <option value="user">User</option>
            <option value="supervisor">Supervisor</option>
            <option value="admin">Admin</option>
        </select>
    </div>

    <label style="display: flex; align-items: center; gap: 8px;">
        <input type="checkbox" name="active" checked>
        <span>Activo</span>
    </label>

    <button type="submit" class="login-btn btn-narrow">Crear</button>
</form>
```

## 7.10 · Lo que **no** hacemos

- No usamos HTML5 `<datalist>` — autocompletado lo construimos como popover custom.
- No hacemos inputs "floating label" estilo Material.
- No añadimos iconos dentro del input (prefijos/sufijos) salvo excepciones muy concretas (`.search-input` del sidebar).
- No usamos `<input type="range">` — la única necesidad (zoom Gantt) se implementa con drag manual.
- No usamos `<input type="file">` visualmente — se oculta y se dispara desde un botón custom (ver `.wiki-edit-file-btn`).
