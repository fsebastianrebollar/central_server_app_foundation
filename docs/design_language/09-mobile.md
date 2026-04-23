# 09 · Responsive y mobile

La app es **primero desktop** (monitor 1920×1080, trabajo técnico con mucho scroll horizontal). El tratamiento mobile es **adaptativo, no re-imaginado**: misma información, mismas celdas, menos chrome.

## 9.1 · Breakpoints

| Breakpoint | Target | Efectos principales |
|---|---|---|
| `≤480px` | Móvil pequeño | Ajustes finos en login, settings modal |
| `≤640px` | **Móvil (principal)** | Sidebar pasa a drawer, cards transparentes, main sin padding lateral, hamburger en header |
| `641-900px` | Tablet portrait | Cards 14px padding, charts 2-col |
| `≤768px` | Logic view / modales específicos | Ver `logic-view.css`, `wiki.css` |
| `901-1024px` | Tablet landscape | Sidebar siempre colapsada por defecto |
| `≤1024px` | **Sidebar colapsada auto** | `width: var(--sidebar-collapsed)` por defecto |
| `≤1100px` | Charts | Grid de charts se simplifica |
| `≤1300px` | Settings | Grid de columnas pasa a stack |
| `≥1600px` | Desktop ultrawide | Se usa en max-widths (history-matrix) |

**No introducir breakpoints nuevos sin motivo documentado.** La dispersión de breakpoints es la peor forma de deuda CSS.

## 9.2 · Reglas estructurales por breakpoint

### `≤1024px` — Tablet / laptop pequeña

```css
@media (max-width: 1024px) {
    .sidebar { width: var(--sidebar-collapsed); }         /* 60px por defecto */
    [data-sidebar="expanded"] .sidebar { width: var(--sidebar-width); }  /* 200px si el usuario la expande */
    .card { padding: 14px 12px; }
    .detail-grid { grid-template-columns: 1fr 1fr; }      /* antes 4 cols */
    .parts-popover { width: min(420px, 92vw); }
    .cbar-popover  { width: min(280px, 92vw); }
    .cell-modal    { max-width: 92vw; }
}
```

Intención: al bajar de 1024, el sidebar pasa a colapsado *por default*. El usuario puede expandirlo puntualmente, pero no es su estado.

### `≤640px` — Mobile

Los tres cambios estructurales:

**1 · Sidebar se convierte en off-canvas drawer**:
```css
@media (max-width: 640px) {
    :root { --sidebar-width: 240px; }        /* un poco más ancha por táctil */

    .sidebar {
        position: fixed;
        top: 52px; left: 0; bottom: 0;
        width: var(--sidebar-width);
        z-index: 95;
        transform: translateX(-100%);         /* oculta por default */
        transition: transform 0.22s ease, width 0s;
        box-shadow: var(--shadow-popup);
    }
    [data-sidebar="expanded"] .sidebar { transform: translateX(0); }
    [data-sidebar="collapsed"] .sidebar { transform: translateX(-100%); }

    .app-header-hamburger { display: flex; }  /* aparece el botón "≡" */

    /* Backdrop oscuro al abrir */
    [data-sidebar="expanded"] .sidebar-backdrop {
        opacity: 1;
        pointer-events: auto;
    }

    /* Evita scroll de body cuando drawer abierto */
    html[data-sidebar="expanded"] body { overflow: hidden; }
}
```

**2 · Cards conservan su identidad visual** (actualizado):
```css
@media (max-width: 640px) {
    main { padding: 8px 10px 72px; }     /* 10px laterales */
    .card {
        background: var(--bg-surface);    /* mismo gris que desktop */
        border: 1px solid var(--border);
        border-radius: 6px;               /* ligeramente más compacto que los 8px de desktop */
        padding: 14px 12px;
        margin: 0;
    }
}
@media (max-width: 480px) {
    .card {
        padding: 12px 10px;
    }
}
```

**Decisión de diseño**: la card en mobile **mantiene** fondo gris, borde y `border-radius`. Priorizamos coherencia visual entre desktop y móvil sobre maximizar el ancho útil. Coste: se pierden ~20px de ancho de contenido (10px padding main por lado), asumido. Antes la card se "disolvía" (transparent + border: none) pero el resultado era ambiguo — no se leía como "panel" sino como texto suelto.

Lo mismo aplica al wiki (`≤768px`), el único otro contenedor principal de la app:

```css
@media (max-width: 768px) {
    .wiki-layout {
        grid-template-columns: 1fr;       /* nav arriba, contenido abajo */
        /* mantiene background, border y border-radius heredados de desktop */
    }
}
```

**3 · Tabla con scroll horizontal dentro de la card**:
```css
.table-wrap {
    overflow-x: auto;
    /* sin margin negativo — la card tiene padding real que contiene la tabla */
}
.table-wrap table {
    width: max-content;       /* crece más allá del viewport si hace falta */
    min-width: 100%;
}
```

En mobile **no** usamos `margin: 0 -10px 0 0` para "hintear" scroll — la card contiene la tabla dentro de su padding. El usuario descubre el scroll por:
- El fade indicator lateral (`.can-scroll-right::after`).
- La tendencia natural a probar arrastre horizontal en tablas anchas.

## 9.3 · Header mobile

```css
@media (max-width: 640px) {
    .app-header {
        padding: 0 12px;
        gap: 8px;
    }
    .app-header-hamburger { display: flex; }      /* botón hamburger */
    .app-header-title {
        font-size: 12px;
        letter-spacing: 0.8px;                    /* ajustado para caber */
    }
    .app-header-user     { display: none; }       /* nombre usuario oculto */
    .app-header .btn-logout,
    .app-header form.inline-form { display: none; }  /* logout va al sidebar user menu */
    .app-header-controls { gap: 6px; }
}
```

**Regla**: el logout "×" del header desaparece en mobile. El usuario hace logout desde el bloque de usuario del sidebar drawer.

## 9.4 · Safe-area insets (iOS notch/home indicator)

```css
@supports (env(safe-area-inset-left)) {
    @media (min-width: 641px) {
        main {
            padding-left: max(24px, env(safe-area-inset-left));
            padding-right: max(24px, env(safe-area-inset-right));
        }
    }
    @media (max-width: 640px) {
        main {
            padding-left: max(10px, env(safe-area-inset-left));
            padding-right: max(10px, env(safe-area-inset-right));
        }
    }
    .view-toolbar {
        margin-bottom: env(safe-area-inset-bottom);
    }
}
```

Patrón clave: **anidamos media queries dentro del `@supports`** porque queremos comportamiento distinto en desktop (padding mínimo 24px) que en mobile (padding mínimo 10px — el que garantiza que las cards no toquen el borde de la pantalla). En ambos casos usamos `max(N, env(...))` para que el inset del notch nunca reduzca el padding por debajo del mínimo visual. **Si cambias esto, prueba en iPhone real** — Simulator a veces no reproduce el inset correctamente.

## 9.5 · Scroll táctil (iOS)

Para que el scroll horizontal en tablas sea fluido en iOS:

```css
@media (max-width: 640px) {
    .table-wrap,
    .modal-body,
    .sidebar-nav,
    .parts-popover,
    .cbar-popover,
    .hm-scroll {
        -webkit-overflow-scrolling: touch;
        touch-action: pan-x pan-y;
    }
}
```

**`touch-action: pan-x pan-y`** es crítico: sin ello iOS hijackea el pan vertical del padre y la tabla no scrollea horizontalmente.

**No uses `body { overflow-x: hidden }`** — rompe el inertial scroll en iOS. Si necesitas evitar overflow del viewport, hazlo sobre `.app-layout` (que ya lo tiene).

## 9.6 · History matrix en mobile

El `history-matrix-table` tiene cabeceras sticky y primera columna sticky en desktop. En mobile las dos conspiran contra el pan horizontal (las sticky cols slide sobre las sticky rows causando glitch visual). **Liberamos todo**:

```css
@media (max-width: 640px) {
    .history-matrix-table thead th,
    .history-matrix-table .hm-step-col,
    .history-matrix-table .hm-step-cell,
    .history-matrix-table thead .hm-step-col {
        position: static;
    }
    .history-matrix-table .hm-step-col,
    .history-matrix-table .hm-step-cell {
        min-width: 180px;
        max-width: 220px;
    }
}
```

Sin esto, en iPhone se ve caos.

## 9.7 · Toolbar flotante en mobile

`.view-toolbar` (bottom: 24px) necesita dos tweaks en mobile:

1. `margin-bottom: env(safe-area-inset-bottom)` — para no chocar con el home indicator.
2. Si el drawer está abierto (`html[data-sidebar="expanded"]`), ocultamos la toolbar para que no solape con el menú:
   ```css
   html[data-sidebar="expanded"] .view-toolbar { display: none; }
   ```

## 9.8 · History strip con scroll snap

```css
.test-history-strip {
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x proximity;
}
.test-history-item {
    scroll-snap-align: start;
}
```

En mobile, el strip de tests históricos se desliza con snap para que cada test quede alineado al borde izquierdo. Mejora notablemente la lectura de historiales largos en pantalla chica.

## 9.9 · Workspace widget en mobile

```css
@media (max-width: 640px) {
    .ws-widget-wrap {
        flex: 1 1 auto;
        min-width: 0;
    }
    .ws-widget {
        max-width: 100%;
    }
    .ws-dropdown {
        width: min(92vw, 320px);
        right: -8px;
    }
}
```

El widget se expande al 100% del ancho disponible, y el dropdown se ajusta para no salir de la pantalla. **El label "WORKSPACE" debe seguir visible** — CLAUDE.md documenta esto como regla de diseño importante.

### Dashboard (sin paddings laterales redundantes)

Como el card principal del dashboard (`.ws-page`) ya tiene su padding interior, **no** añadimos padding lateral adicional a `.ws-grid`, `.ws-section`, ni `.dashboard-hero`:

```css
@media (max-width: 640px) {
    .ws-grid       { gap: 12px; }          /* sin padding lateral */
    .dashboard-hero { margin: 12px 0; }    /* sin margin lateral */
    /* .ws-section: sin override */
}
```

La respiración lateral viene del `main { padding: 8px 10px 72px }` que afecta a todo el contenido de la página.

## 9.10 · Lo que **no** es responsive

Hay componentes que no tienen tratamiento mobile porque **no se usan en mobile**:

- **`/search`** con vista Joined y Steps: la densidad de info es irreducible. En mobile la experiencia es sub-óptima por diseño.
- **Gantt Time view**: SVG con dimensiones fijas, sin zoom touch. Funciona, pero no es cómodo.
- **History matrix**: lo mínimo funciona, la experiencia ideal es desktop.
- **Charts con muchas series**: bajan a 2 columnas, pero pie/funnel complejos siguen siendo mejor en desktop.

Si un cliente se quejara de uno de estos en mobile, la respuesta debe ser "¿tienes acceso a un portátil?" antes que "lo rediseñamos mobile-first". La app es un **dashboard de fábrica**, no un feed social.

## 9.11 · Testing responsive

Workflow recomendado:
1. **Chrome DevTools**: iPhone 12 Pro (390×844), iPad Mini (744×1133), iPhone SE (375×667).
2. **iPhone real** vía Telegram screenshot bot (ver CLAUDE.md global): `/screenshot dashboard en móvil`.
3. **Lighthouse mobile audit** ocasional para chequear touch target sizes.

No uses resoluciones "custom" — apégate a devices reales.
