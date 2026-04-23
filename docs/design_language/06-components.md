# 06 · Componentes

Catálogo de los patrones visuales reutilizables. Para cada uno se indica propósito, anatomía, variantes y los estados (hover/active/disabled). Los snippets CSS canónicos viven en `snippets/`.

## Tabla de contenidos

1. [Botones](#botones)
2. [Cards](#cards)
3. [Tablas](#tablas)
4. [Badges](#badges)
5. [Modales](#modales)
6. [Tooltips](#tooltips)
7. [Flash messages / toasts](#flash-messages--toasts)
8. [Paginación](#paginación)
9. [View toolbar flotante](#view-toolbar-flotante)
10. [Pills (filter bar y column bar)](#pills-filter-bar-y-column-bar)
11. [Dropdowns y popovers](#dropdowns-y-popovers)
12. [Workspace widget](#workspace-widget)
13. [Test history strip](#test-history-strip)
14. [Sort tabs](#sort-tabs)

---

## Botones

### Taxonomía

La app usa tres tipos de botones:

| Tipo | Apariencia | Cuándo |
|---|---|---|
| **Outline (default)** | Fondo transparente, `1px solid var(--border)`, hover: neón | Acciones secundarias, toggle, reset, close, back |
| **Primary (filled)** | Fondo `--neon`, texto `#fff` | Acción principal de un flujo (save, apply, login, submit) |
| **Danger** | Transparente, border + texto `--error-text` | Borrar, acciones destructivas |

### Patrón Outline (estándar)

```css
.btn-back {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 6px 14px;
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 12px; font-weight: 600;
    font-family: inherit;
    transition: all 0.2s;
}
.btn-back:hover {
    border-color: var(--neon);
    color: var(--neon-text);
    box-shadow: 0 0 8px var(--neon-subtle);
}
```

**Dimensiones estándar**:
- Botón normal: `padding: 6px 14px`, `font-size: 12px`, `font-weight: 600`, `border-radius: 4px`.
- Botón pequeño (pill): `padding: 4px 10-12px`, `font-size: 11px`.
- Botón circular (icono): `34×34px`, `border-radius: 50%`.

### Patrón Primary

```css
.login-btn {
    padding: 10px 20px;
    background: var(--neon);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 14px; font-weight: 600;
    transition: opacity 0.15s;
}
.login-btn:hover { opacity: 0.85; }
```

Nota: los primary **no** cambian de color en hover — solo bajan opacity a 0.85. El color neón ya es intenso, no hace falta más.

Variantes: `.fbar-apply`, `.ws-modal-btn-primary`, `.view-toolbar-btn-active`, `.pagination-btn-active`.

### Patrón Danger

```css
.btn-danger {
    background: transparent;
    border: 1px solid var(--error-text);
    color: var(--error-text);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 12px; font-weight: 600;
    transition: all 0.15s;
}
.btn-danger:hover {
    background: var(--error-bg);
    box-shadow: 0 0 8px rgba(255, 0, 0, 0.2);
}
```

### Botones circulares del header

```css
.btn-lang, .theme-toggle {
    width: 34px; height: 34px;
    border-radius: 50%;
    border: 1px solid var(--border);
    background: transparent;
    display: flex; align-items: center; justify-content: center;
    font-family: inherit;
    transition: all 0.2s;
}
.btn-lang:hover, .theme-toggle:hover {
    border-color: var(--neon);
    color: var(--neon-text);
    box-shadow: 0 0 8px var(--neon-subtle);
}
```

### Botón "dirty" (naranja discreto)

Cuando algo necesita ser guardado se usa un border/fondo naranja **sutil** más un punto de estado. Ver `.fbar-apply-dirty` y `.ws-widget-dirty`.

### Regla

**No crees botones con fondo sólido que no sean primary o danger.** Si te tienta un botón azul, un botón gris sólido, un botón con gradiente — para, revisa el contexto y elige outline o primary.

---

## Cards

```css
.card {
    background: var(--bg-surface);
    padding: 24px;
    border-radius: 8px;
    border: 1px solid var(--border);
}
```

- **Sin sombra por defecto** (ver excepción en 4.4).
- Padding 24px en desktop, 14-12 px en mobile.
- Radius `8px` (casi todos los elementos); el modal de celda usa `12px` para distinguirse.

### Card heading

```css
.card h2 {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px;
}
.card h2::before {
    content: "//";
    color: var(--neon);
    font-weight: 800;
    font-size: 20px;
    letter-spacing: -1px;
}
```

**Firma visual de la app**: el `//` antes de cada título. No lo omitas.

### Secciones internas (`.card-section`)

```css
.card-section {
    padding-bottom: 24px;
    margin-bottom: 24px;
    border-bottom: 1px solid var(--border);
}
.card-section-last { /* sin border-bottom */ }
```

Cada sección lleva un `<h3>` propio (no `//` prefix) como subtítulo.

### Cards elevadas (workspace, test-history, dashboard)

Algunas cards sí usan sombra porque son "clicables y destacadas":

```css
.ws-card, .test-history-item {
    /* base: igual que card */
    transition: transform 0.14s, border-color 0.14s, box-shadow 0.14s;
}
.ws-card:hover, .test-history-item:hover {
    transform: translateY(-2px);
    border-color: var(--border-hover);
    box-shadow: var(--shadow-card-hover);
}
```

El patrón es: lift de 2px + border más oscuro + sombra incremental.

---

## Tablas

```css
table {
    width: max-content;
    min-width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
th, td {
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
th {
    background: var(--table-header-bg);
    font-size: 12px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
    color: var(--text-secondary);
    position: sticky; top: 0;
}
tbody tr:nth-child(even) { background: var(--table-row-alt); }
tbody tr:hover { background: var(--table-hover); }
.clickable-row:hover { background: var(--neon-subtle); }
.row-ok   { border-left: 5px solid #16a34a; }
.row-fail { border-left: 5px solid #dc2626; }
```

### Detalles importantes

- **Width: `max-content` + `min-width: 100%`** → la tabla expande lo que necesiten las columnas; si cabe, ocupa el 100%, si no, fuerza scroll horizontal.
- **Zebra discreta**: alphas de 0.015 (claro) / 0.018 (oscuro). Es casi imperceptible, solo ayuda a seguir filas en rangos largos.
- **Hover acumulativo**: la fila par con zebra + hover sigue legible porque los alphas son aditivos suaves.
- **Fila clicable**: `.clickable-row` usa `--neon-subtle` en hover (más naranja) para distinguir de filas no clicables.
- **Indicador de resultado**: 5px de border-left en verde/rojo puro (no vía variable). Es el único lugar donde colores hardcodeados están permitidos por coherencia visual cross-theme.

### Column max-widths

Columnas con texto potencialmente largo tienen max-width específico para forzar truncado:

```css
td.col-id, td.col-bench_id, td.col-item, ... { max-width: 80px; }
td.col-prod_number, td.col-operator, ...       { max-width: 120px; }
td.col-model, td.col-start_dt, ...            { max-width: 160px; }
td.col-name, td.col-message, ...              { max-width: 200px; }
td.col-value, td.col-valid_values, ...        { max-width: 180px; }
/* todas llevan: */
overflow: hidden; text-overflow: ellipsis;
```

Truncar hace aparecer la clase `.cell-truncated`, que cambia cursor a pointer y en hover pasa a `color: var(--neon)`. Al hacer click se abre el `.cell-modal` con el valor completo.

### Scroll fade indicators

Cuando la tabla tiene scroll horizontal, `.table-wrap` puede recibir `.can-scroll-left` / `.can-scroll-right` (setado por JS). Eso activa gradientes laterales:

```css
.table-wrap.can-scroll-right::after {
    content: '';
    position: sticky; right: 0; top: 0; bottom: 0;
    width: 32px;
    pointer-events: none;
    background: linear-gradient(to right, transparent, var(--bg-surface));
    float: right; margin-top: -100%;
    height: 100%; z-index: 2;
}
/* análogo para ::before con can-scroll-left */
```

### Sortable headers

```css
th.sortable { cursor: pointer; user-select: none; position: relative; padding-right: 22px; }
th.sortable:hover { color: var(--neon); }
th.sortable .sort-indicator {
    position: absolute; right: 4px; top: 50%;
    transform: translateY(-50%);
    font-size: 10px;
    color: var(--text-secondary);
    opacity: 0;
    transition: opacity 0.15s;
}
th.sortable:hover .sort-indicator { opacity: 0.4; }
th.sort-active .sort-indicator { opacity: 1; color: var(--neon); }
```

La flecha `▲▼` es invisible hasta el hover (0.4) o hasta que está activa (1, naranja).

---

## Badges

Píldoras pequeñas para estado, recuento, categoría:

```css
.badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 12px; font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-ok { background: var(--success-bg); color: var(--success-text); border: 1px solid var(--success-border); }
.badge-fail { background: var(--error-bg); color: var(--error-text); border: 1px solid var(--error-border); }
.badge-other { background: var(--input-bg); color: var(--text-secondary); border: 1px solid var(--border); }
```

- **Siempre llevan 1px de border** matching el color del fondo+text. Sin borde se sienten "flotantes"; con borde quedan ancladas.
- `padding: 3px 9px` es el canónico. No modifiques.
- Pseudo-variantes semánticas en logic view: `.logic-step-badge-parallel` (neón azul), `.logic-step-badge-critical` (rojo), `.logic-step-badge-branch` (usa `--branch-color`).

---

## Modales

### Estructura común

```html
<div class="modal-overlay modal-open">
  <div class="modal-box">
    <div class="modal-header">
      <h3>Título</h3>
      <button class="modal-close">×</button>
    </div>
    <div class="modal-body">...</div>
    <div class="modal-footer">
      <button>Cancelar</button>
      <button class="login-btn">Aceptar</button>
    </div>
  </div>
</div>
```

### CSS

```css
.modal-overlay {
    position: fixed; inset: 0;
    background: var(--overlay-bg);
    backdrop-filter: blur(4px);
    z-index: 300;
    display: none;
    justify-content: center; align-items: center;
}
.modal-overlay.modal-open { display: flex; }

.modal-box {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    width: 100%; max-width: 480px; max-height: 80vh;
    display: flex; flex-direction: column;
    box-shadow: 0 8px 40px var(--modal-shadow), 0 0 12px var(--neon-glow);
}
.modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
}
.modal-header h3 { font-size: 14px; font-weight: 600; }
.modal-close {
    width: 28px; height: 28px;
    border: 1px solid var(--border); border-radius: 4px;
    background: transparent;
    font-family: inherit;
    transition: all 0.15s;
    display: flex; align-items: center; justify-content: center;
}
.modal-close:hover {
    background: var(--error-bg);
    color: var(--error-text);
    border-color: var(--error-border);
}
.modal-body { padding: 16px 20px; overflow-y: auto; flex: 1; }
.modal-footer {
    padding: 12px 20px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: flex-end; align-items: center; gap: 8px;
}
```

### Reglas

- **Clase de "abierto" es `.modal-open`** (sobre `.modal-overlay`). **NO `.active`**. Mezclar las dos es fuente de bugs reales (ver CLAUDE.md → Cache Manager, Service Control).
- El overlay lleva `backdrop-filter: blur(4px)` para difuminar el contenido de fondo.
- El `.modal-box` lleva doble sombra: una base (`--modal-shadow`) y un glow neón sutil (`--neon-glow`). Es la única sombra "decorativa" del sistema.
- Max-width default 480px; hay tallas específicas documentadas en `04-layout.md §4.6`.

### Variante `.cell-modal`

Para valores largos de celda (popup al hacer click en una celda truncada). Tiene `border-radius: 12px` (más grande que el estándar) y max-width 600px. `.cell-modal-header h4` también lleva el `//` naranja.

---

## Tooltips

### Tooltip de celda (hover)

```css
.cell-tooltip {
    position: fixed;
    z-index: 1100;
    max-width: 420px;
    max-height: 200px;
    overflow-y: auto;
    padding: 8px 12px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    font-size: 12px;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
    pointer-events: none;
}
```

### Tooltip de logic view / Gantt

Similar pero con `--neon-subtle` glow adicional (ver `logic-view.css` → `.logic-tooltip`).

Regla general: tooltips son `pointer-events: none` para no bloquear clicks.

---

## Flash messages / toasts

### Inline (dentro de contenedor)

```css
.flash {
    padding: 10px 16px;
    border-radius: 4px;
    font-size: 12px; font-weight: 500;
    margin-bottom: 8px;
}
.flash-success { background: var(--success-bg); color: var(--success-text); border: 1px solid var(--success-border); }
.flash-error   { background: var(--error-bg);   color: var(--error-text);   border: 1px solid var(--error-border); }
```

### Toast (flotante top-right)

```css
.flash-toast {
    position: fixed;
    top: 68px;              /* 52 header + 16 gap */
    right: 24px;
    z-index: 9999;
    max-width: 420px;
    display: flex; flex-direction: column; gap: 8px;
    pointer-events: none;
    animation: flash-toast-in 0.25s ease-out;
}
.flash-toast .flash { pointer-events: auto; box-shadow: var(--shadow-popup); }
.flash-toast-hide { opacity: 0; transform: translateY(-8px); transition: opacity 0.35s, transform 0.35s; }

@keyframes flash-toast-in {
    from { opacity: 0; transform: translateY(-12px); }
    to   { opacity: 1; transform: translateY(0); }
}
```

Auto-dismiss por JS a los ~3-5s (según tipo).

---

## Paginación

```css
.pagination { display: flex; justify-content: center; gap: 4px; margin-top: 12px; }
.pagination-btn {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 32px; height: 32px;
    padding: 0 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text);
    font-size: 12px; font-weight: 500;
    transition: all 0.15s;
}
.pagination-btn:hover { border-color: var(--neon); color: var(--neon); }
.pagination-btn-active {
    background: var(--neon); border-color: var(--neon); color: #fff;
    cursor: default;
}
.pagination-btn-disabled { opacity: 0.35; cursor: default; pointer-events: none; }
.pagination-ellipsis {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 24px; height: 32px;
    color: var(--text-secondary); font-size: 14px;
}
```

Por encima va `.pagination-info` / `.pagination-summary` (texto mono, alineado a la derecha).

Por debajo va `.table-export-bar` con links `sql · csv · pdf` separados por `·` en gris, hover → `var(--accent)`.

---

## View toolbar flotante

La "isla" naranja en el centro-abajo (`/search` para cambiar de vista, `/test` para cambiar de modo Table/Time/Logic, `/reports` para product filter).

```css
.view-toolbar {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 900;
    pointer-events: none;
}
.view-toolbar-pill {
    display: flex; align-items: center; gap: 2px;
    padding: 4px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18), 0 0 0 1px var(--border);
    backdrop-filter: blur(16px);
    pointer-events: auto;
}
[data-theme="dark"] .view-toolbar-pill {
    background: rgba(20, 20, 25, 0.92);
    box-shadow: 0 4px 24px rgba(0,0,0,0.5), 0 0 0 1px var(--border);
}
.view-toolbar-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 8px 16px;
    border-radius: 22px;
    border: none; background: transparent;
    color: var(--text-secondary);
    font-size: 12px; font-weight: 500;
    font-family: inherit;
    transition: all 0.2s;
}
.view-toolbar-btn:hover { color: var(--text); background: var(--neon-subtle); }
.view-toolbar-btn-active { background: var(--neon); color: #fff; font-weight: 600; }
.view-toolbar-label {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
```

Es un componente flotante, sticky, con glassmorphism. El `pointer-events: none` en el wrapper + `pointer-events: auto` en el pill es deliberado: permite hacer scroll/click sobre la página a través del espacio que rodea a la toolbar.

---

## Pills (filter bar y column bar)

Las pills aparecen en dos barras: la **filter bar** (`.fbar`) y la **column bar** (`.cbar`). Cada pill es una condición/columna arrastrable.

### Filter pills

```css
.fbar-pill {
    display: inline-flex; align-items: center;
    padding: 3px 6px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 11px;
    cursor: grab;
    transition: all 0.15s;
}
.fbar-pill-test .fbar-pill-tag { background: var(--neon-subtle); color: var(--neon-text); }
.fbar-pill-step .fbar-pill-tag { background: rgba(0, 144, 224, 0.10); color: var(--neon-blue); }
.fbar-pill:hover { border-color: var(--border-hover); }
.fbar-pill:active { cursor: grabbing; }
.fbar-pill-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--error-text); /* punto rojo para eliminar */
    opacity: 0; /* invisible hasta hover */
}
.fbar-pill:hover .fbar-pill-dot { opacity: 0.5; }
.fbar-pill-dot:hover { opacity: 1; }
```

- **Pills de test filter**: tag naranja.
- **Pills de step filter**: tag azul.
- **Drag**: cursor grab/grabbing. Drop targets tienen `.fbar-pill-drop-target` con outline neón.
- **Delete**: dot rojo aparece en hover; click pregunta confirmación en el `.filter-delete-modal`.

### Column pills (`.cbar-pill`)

Más simples — son solo la columna visible, sin tag de tipo. Comparten `.fbar-pill-dot` para eliminar.

### Filter presets

```css
.fbar-preset {
    background: transparent;
    border: none; border-right: 1px solid var(--border);
    padding: 6px 12px;
    color: var(--text-secondary);
    font-size: 11px; font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    transition: color 0.15s, background 0.15s;
}
.fbar-preset:hover { color: var(--text); background: rgba(255, 106, 0, 0.04); }
.fbar-preset-on {
    background: var(--neon-subtle);
    color: var(--neon-text);
    font-weight: 700;
}
```

Los presets (Hoy, Semana, Mes, Custom…) viven como segmented control con separadores verticales.

---

## Dropdowns y popovers

Patrón común:

```css
.foo-dropdown {
    position: absolute;
    top: calc(100% + 4px);
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    z-index: 200;
    box-shadow: var(--shadow-popup);
    display: none;
}
.foo-dropdown.open { display: flex; flex-direction: column; }
.foo-dropdown-item {
    padding: 8px 16px;
    font-size: 12px; font-weight: 600;
    color: var(--text-secondary);
    transition: background 0.15s, color 0.15s;
}
.foo-dropdown-item:hover {
    background: var(--neon-subtle);
    color: var(--neon-text);
}
```

Ejemplos: `.lang-dropdown-menu`, `.ws-dropdown`, `.cond-dd-*`.

### Popovers

Los popovers (column add, filter condition) son similares pero con `padding: 12px` y `min-width` específico. Ver `.cbar-popover`, `.parts-popover`, `.cond-op-grid-panel`.

---

## Workspace widget

Component flotante bottom-left en dashboard, search, test detail. Muestra el workspace activo con indicador de dirty.

```css
.ws-widget {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 22px;
    box-shadow: var(--shadow-popup);
    cursor: pointer;
    transition: all 0.15s;
}
.ws-widget-btn:hover { border-color: var(--neon); }
.ws-widget-dirty {
    /* pequeño círculo naranja indicando cambios no guardados */
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--neon);
    box-shadow: 0 0 6px var(--neon-glow);
}
```

Dropdown asociado (`.ws-dropdown`):
- Sections: "PUBLIC" / "PRIVATE" / "DEFAULT".
- Items con hover neón-subtle.
- Footer con actions: Save / Save as… / Rename / Delete.
- Acciones destructivas usan `.ws-dropdown-action-danger` (texto rojo).

---

## Test history strip

Tira horizontal de "cards de tests anteriores" en la página /test. Cada item:

```css
.test-history-item {
    flex: 0 0 auto;
    display: flex; gap: 10px;
    min-width: 220px;
    padding: 10px 14px 10px 12px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: transform 0.14s, border-color 0.14s, box-shadow 0.14s;
}
.test-history-item:hover {
    transform: translateY(-2px);
    border-color: var(--border-hover);
    box-shadow: var(--shadow-card-hover);
}
.test-history-item-active {
    border-color: var(--neon);
    background: var(--neon-subtle);
    box-shadow: 0 0 0 1px var(--neon), 0 6px 20px -10px var(--neon-glow);
}
.test-history-dot {
    flex: 0 0 4px;
    border-radius: 2px;
    align-self: stretch;
}
.test-history-item-ok   .test-history-dot { background: var(--success-text); }
.test-history-item-fail .test-history-dot { background: var(--error-text); }
```

El dot vertical (4px de ancho, altura completa del item) es el indicador de resultado. Más sutil que el border-left 5px de las filas de tabla.

---

## Sort tabs

Cuando una vista ofrece varias opciones de ordenación tabuladas (admin panels):

```css
.sort-tabs {
    display: inline-flex;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
    margin: 12px 0 10px;
}
.sort-tab {
    background: transparent;
    border: none;
    border-right: 1px solid var(--border);
    padding: 6px 14px;
    font-family: inherit;
    font-size: 12px;
    /* hover + active similar al preset filter */
}
```

---

## Reglas de oro para componentes nuevos

1. **Reutiliza el patrón más cercano.** Si ya hay un tooltip, no inventes un tooltip distinto.
2. **Padding y radius dentro de la escala canónica.** Los valores 4/6/8/12 son los radius usados; 4/6/8/10/12/14/16/20/24 los paddings/gaps. No introduzcas 7 o 13 salvo razón.
3. **Todos los elementos interactivos llevan `transition`** — 0.15s default, 0.2s para elementos con más "peso", 0.14s para hover de cards elevadas.
4. **`font-family: inherit` obligatorio** en `button`, `input`, `textarea`, `select`. Sin eso, el navegador les mete sans-serif del sistema.
5. **Los componentes nuevos empiezan en `snippets/`**. Copia el snippet más parecido, modifícalo, y cuando esté en producción actualiza la guía.
