# 03 · Tipografía

## 3.1 · Stack único

```css
font-family: "SF Mono", "Fira Code", "Consolas", "JetBrains Mono", monospace;
```

**Toda la UI es monospace.** Definido en `body` y heredado por inputs/botones vía `font-family: inherit`. No hay sans-serif. No hay serif. Si un componente rompe la herencia, es un bug.

### Excepción controlada

Algunos componentes **reafirman** el stack explícitamente con una variante ampliada que incluye `'Cascadia Code'`:

```css
font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
```

Aparece en `.cell-tooltip`, `.cell-modal-header h4`, `.cell-modal-body`, `.pagination-summary`, `.view-toolbar-label`, `.test-view-steps-count`. Es funcionalmente equivalente en macOS y Windows; considéralo la forma "canónica" para componentes nuevos donde quieras hacer explícito el look tipográfico.

## 3.2 · Escala de tamaños

| Tamaño | Dónde se usa | Peso | Extras |
|---|---|---|---|
| `9px` | `.admin-badge-sm`, `.guest-badge-sm` (indicadores de rol en sidebar) | 700 | `text-transform: uppercase`, `letter-spacing: 0.5px` |
| `10px` | Chips de bench, step-item en history matrix, tick labels Gantt | 700 | Uppercase + letter-spacing |
| `11px` | `.test-history-*`, `.step-count`, `.logic-step-badge`, dashboards compactos | 500-700 | |
| `12px` | `th` (table header), `.badge`, `.fbar-pill`, `.view-toolbar-btn`, botones estándar, `.flash` | 500-700 | Uppercase + letter-spacing en `th` y `view-toolbar-label` |
| `13px` | **Base del cuerpo de la app**: `td`, `.sidebar-link`, `.text-secondary`, `.mono`, `.cell-modal-body` | 400-500 | |
| `14px` | `.modal-header h3`, `.login-btn`, `.btn-logout`, `.theme-toggle`, iconos | 500-700 | |
| `15px` | `.sidebar-avatar` | 700 | |
| `16px` | `.card h2` (antes de ajuste) / iconos redondeados | 600-700 | |
| `18px` | `.card h2` actual, `.login-title` | 600-700 | Uppercase + letter-spacing 3px en `.card h2` |
| `20px` | `.card h2::before` (el `//` decorativo), `.sidebar-icon` | 800 | |

**Prohibido ≥ 22px** salvo en el `.dashboard-hero` (landing). La app es densa a propósito.

## 3.3 · Pesos

- `400` → texto normal (body de tabla, hints).
- `500` → texto acentuado suave (`.sidebar-link`, `.flash`, `.logic-step-name`).
- `600` → default del "énfasis": labels, badges, botones estándar, `th`, títulos secundarios.
- `700` → títulos importantes, brand del header, resultados, `.card h2`.
- `800-900` → casos extremos: `//` decorativo del `.card h2::before`, logo del header.

## 3.4 · Espaciado de letras y transformaciones

El patrón "uppercase + letter-spacing" es una firma visual recurrente:

| Patrón | letter-spacing | Dónde |
|---|---|---|
| Branding / header title | `1.2px` | `.app-header-title` |
| Títulos de card | `3px` | `.card h2` |
| Table headers | `0.5px` | `th` |
| Badges | `0.3px` | `.badge` |
| Section labels del logic view | `0.5px` | `.logic-step-checker`, `.logic-step-badge-result` |
| Pills, botones uppercase chicos | `0.06em` / `0.5-1.4px` | `.view-toolbar-label`, `.test-history-label-text`, `.test-history-fullbtn` |

Regla rápida: texto uppercase siempre lleva `letter-spacing`. Más uppercase, más letter-spacing. Texto normal en lowercase casi nunca lo lleva.

## 3.5 · Clases utilitarias tipográficas

```css
.text-secondary {  /* texto atenuado corto */
    color: var(--text-secondary);
    font-size: 13px;
}

.mono {  /* marcado explícito como "estilo código" */
    font-family: inherit;          /* ya es monospace */
    font-size: 13px;
    color: var(--text-secondary);
}
```

`.mono` es semántica: aunque el stack ya es monospace, la clase marca el elemento como "esto es un valor técnico/código" (IDs, timestamps, rutas, hashes). Los screen readers no lo diferencian pero el código del futuro sí sabrá a qué aferrarse.

## 3.6 · Scrollbars

En la `test-history-strip` y `logic-minimap`:

```css
scrollbar-width: thin;
scrollbar-color: var(--border) transparent;
```

WebKit/Blink version:
```css
::-webkit-scrollbar { height: 6px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
```

Son scrollbars delgadas, teñidas con el color del borde, sin botones laterales. Complementan la estética densa.
