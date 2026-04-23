# 02 · Tokens y theming

Todos los colores, tamaños de layout y sombras son **custom properties CSS** definidos en `:root` (claro, default) y redefinidos en `[data-theme="dark"]`. Nunca hardcodees un color en un componente — siempre a través de variable.

El cambio de tema se hace mutando el atributo `data-theme` en `<html>`. Un script inline en `<head>` de `base.html` lee `localStorage` y aplica el valor **antes del primer paint**, evitando flash blanco.

## 2.1 · Tabla completa de tokens

### Superficies y texto

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` | `#f4f3f0` | `#0a0a0f` | Fondo de `<body>` |
| `--bg-surface` | `#fdfcfa` | `#141419` | Cards, modales, popovers, sidebar, dropdowns |
| `--bg-header` | `rgba(253,252,250,0.78)` | `rgba(10,10,15,0.82)` | Header con glassmorphism (backdrop-filter) |
| `--header-text` | `#2c2c30` | `#e4e4e7` | Texto del header (ligeramente atenuado en branding) |
| `--text` | `#2c2c30` | `#e4e4e7` | Texto primario |
| `--text-secondary` | `#85858d` | `#8a8a94` | Labels, hints, `.mono`, iconos neutros |

### Bordes

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--border` | `#e6e4e1` | `#2e2e34` | Borde por defecto (cards, tablas, inputs) |
| `--border-hover` | `#c8c5c1` | `#46464d` | Borde al pasar el ratón sobre elementos no interactivos clave |

### Formularios y tablas

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--input-bg` | `#f7f6f3` | `#1a1a20` | `input`, `select`, `textarea`, `th`, `.back-arrow` |
| `--table-header-bg` | `var(--input-bg)` | `#1f1f26` | Fondo de `<th>` |
| `--table-row-alt` | `rgba(0,0,0,0.015)` | `rgba(255,255,255,0.018)` | Fila par (zebra) |
| `--table-hover` | `rgba(0,0,0,0.025)` | `rgba(255,255,255,0.035)` | Hover sobre fila |

### Acento neón naranja (marca)

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--neon` | `#ff6a00` | `#ff6a00` | Color de marca, borde activo, focus, fill de botones primarios |
| `--neon-glow` | `rgba(255,106,0,0.18)` | `rgba(255,106,0,0.4)` | Sombras de glow en hover / estados activos |
| `--neon-subtle` | `rgba(255,106,0,0.07)` | `rgba(255,106,0,0.08)` | Fondo sutil en hover / filas clicables |
| `--neon-text` | `#c85500` | `#ff6a00` | Texto accent (más oscuro en claro por legibilidad) |

> **Nota importante**: `--neon-text` es **el único token que no es bi-direccional simétrico**: en claro se oscurece a `#c85500` para mantener contraste AA sobre `--bg-surface`. Úsalo cuando quieras texto de color acento. Para backgrounds/border usa `--neon`.

### Acento neón azul (secundario, puntual)

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--neon-blue` | `#0090e0` | `#00c8ff` | Secundario: badges "parallel", `:focus` de filter-date, chart palette secundaria |
| `--neon-blue-glow` | `rgba(0,144,224,0.18)` | `rgba(0,200,255,0.35)` | Glow del accent azul |

### Estados semánticos

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--success-bg` | `#eaf6ee` | `#052e16` | Fondo badge/flash OK |
| `--success-text` | `#1a6b4a` | `#86efac` | Texto badge/flash OK, dot de fila OK |
| `--success-border` | `#bfe8cd` | `#14532d` | Borde badge OK |
| `--error-bg` | `#fdf1f1` | `#450a0a` | Fondo badge/flash FAIL |
| `--error-text` | `#9e2a2a` | `#fca5a5` | Texto badge/flash FAIL, dot de fila FAIL |
| `--error-border` | `#f5d0d0` | `#7f1d1d` | Borde badge FAIL |

### Overlays y sombras

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--overlay-bg` | `rgba(0,0,0,0.32)` | `rgba(0,0,0,0.55)` | Fondo semitransparente de `.modal-overlay` |
| `--modal-shadow` | `rgba(0,0,0,0.12)` | `rgba(0,0,0,0.4)` | Sombra base del `.modal-box` |
| `--shadow-card` | `0 1px 4px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03)` | `0 4px 16px rgba(0,0,0,0.35)` | Cards elevadas (poco usado — preferimos borde) |
| `--shadow-card-hover` | `0 4px 16px rgba(0,0,0,0.07)` | `0 6px 20px rgba(0,0,0,0.45)` | Hover de cards elevadas (workspace cards, test history) |
| `--shadow-popup` | `0 4px 20px rgba(0,0,0,0.08)` | `0 8px 32px rgba(0,0,0,0.35)` | Dropdowns, popovers, cell tooltips |
| `--shadow-modal` | `0 8px 32px rgba(0,0,0,0.10)` | `0 8px 32px rgba(0,0,0,0.45)` | Modales full (poco usado — ya combinamos modal-shadow + neon-glow) |

### Layout

| Variable | Valor | Uso |
|---|---|---|
| `--sidebar-width` | `200px` (desktop) / `240px` (mobile) | Ancho de la sidebar expandida |
| `--sidebar-collapsed` | `60px` | Ancho de la sidebar colapsada |

## 2.2 · Filosofía de softening claro vs oscuro

Los valores de sombra en claro son **deliberadamente suaves** (alphas 0.03-0.12) para lograr una lectura "relajada y poco fatigante". En oscuro, los alphas suben (0.35-0.45) porque sobre fondos casi negros las sombras compiten menos y se necesita más opacidad para que se perciban.

Los valores de `--neon-glow` siguen la misma regla: `0.18` en claro vs `0.4` en oscuro.

## 2.3 · Añadir una variable nueva

Si un componente requiere un color no cubierto:

1. Define la variable en **ambos** `:root` **y** `[data-theme="dark"]` en `style.css`.
2. Úsala semánticamente — `--bg-foo` para un fondo, `--text-foo` para un texto.
3. Actualiza la tabla en este archivo.
4. Si el valor solo tiene sentido en uno de los temas, igual define la variable en los dos (el otro hereda o repite).

## 2.4 · Variables exclusivas del Logic view

`app/static/css/logic-view.css` define cuatro tokens adicionales:

| Variable | Claro | Oscuro | Uso |
|---|---|---|---|
| `--pipeline` | `#c8c8cc` | `#27272a` | Tubería vertical central + dots del pipeline |
| `--error-icon` | `#dc2626` | `#f87171` | Icono crítico en step card |
| `--warning-icon` | `#d97706` | `#fbbf24` | (Reservado, no se usa todavía en step cards) |
| `--info-icon` | `#0891b2` | `#22d3ee` | (Reservado) |

La branch color por segmento se setea vía `--branch-color` inline (JS) en el elemento contenedor, y se usa con `color-mix()` para generar fondos y bordes atenuados.

## 2.5 · El preload guard

```css
html.preload, html.preload *, html.preload *::before, html.preload *::after {
    transition: none !important;
    animation-duration: 0s !important;
    animation-delay: 0s !important;
}
```

`base.html` añade la clase `preload` inline en `<head>` y la elimina tras `window.load`. Esto mata transiciones durante el primer paint para que sidebar, drawer y toggles no se "animen desde un estado obsoleto" al cargar.
