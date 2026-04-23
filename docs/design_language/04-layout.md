# 04 · Layout

## 4.1 · Árbol de DOM general

```
<html data-theme="dark|light" data-sidebar="expanded|collapsed">
  <body>
    <header class="app-header">...</header>    ← 52px, sticky, glassmorphism
    <div class="app-layout">                   ← flex row, height: calc(100vh - 52px)
      <aside class="sidebar">...</aside>        ← 200px expanded, 60px collapsed
      <main>                                    ← flex: 1, overflow-y: auto
        <section class="card">...</section>
      </main>
    </div>
  </body>
</html>
```

Esta estructura se mantiene en **todas** las páginas internas (/dashboard, /search, /test, /settings, /reports, /wiki, /user). Solo `/login` y `/setup` usan un layout centrado distinto (`.login-container`).

## 4.2 · Header

```css
.app-header {
    background: var(--bg-header);       /* rgba con alpha */
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    padding: 0 20px;
    height: 52px;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px;
}
```

- **Altura fija**: 52px. No negociable — layout depende de este valor (`height: calc(100vh - 52px)` en `.app-layout`, `top: 68px` en toasts).
- **Glassmorphism**: backdrop-blur de 14px + fondo semitransparente. Se ve el scroll difuminado por detrás. En oscuro el alpha sube a `0.82` para que no se "coma" el contenido.
- **Sticky**: siempre visible, `z-index: 100`.

### Logo brand

```css
.app-header-logo {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: var(--neon);
    color: #000;
    font-weight: 900;
    box-shadow: 0 0 10px var(--neon-glow);
    display: flex; align-items: center; justify-content: center;
}
```

Cuadrado 28px con esquinas redondeadas 6px, fondo neón, texto negro 900, glow sutil. Es **el único** lugar donde un fondo de color lleva texto negro (`#000`). Esa elección crea el contraste máximo que define la marca.

### Título brand

```css
.app-header-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}
```

### Controles derecha

Grupo `.app-header-controls` contiene (en orden, de izquierda a derecha):
1. `.app-header-user` — texto "HOLA, nombre" atenuado (`opacity: 0.7`).
2. `.btn-logout` — icono `×`, atenuado, hover → `--error-text`.
3. `.btn-lang` — selector de idioma (ES/EN/DE), círculo 34×34 con `font-weight: 700`.
4. `.theme-toggle` — sol/luna, círculo 34×34.

Todos los botones redondos del header (`.btn-lang`, `.theme-toggle`) comparten:
- `34×34px`, `border-radius: 50%`.
- `border: 1px solid var(--border)`, `background: transparent`.
- Hover: `border-color: var(--neon)`, `color: var(--neon-text)`, `box-shadow: 0 0 8px var(--neon-subtle)`.

## 4.3 · Sidebar

```css
.sidebar {
    width: var(--sidebar-width);        /* 200px */
    background: var(--bg-surface);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    transition: width 0.2s;
    overflow: hidden;
}
[data-sidebar="collapsed"] .sidebar {
    width: var(--sidebar-collapsed);    /* 60px */
}
```

- **Dos estados**: expandida (200px) y colapsada (60px). El estado se persiste en `localStorage` y se refleja en `data-sidebar` sobre `<html>`.
- Al colapsar: las labels se ocultan (`display: none`), los links se centran y el chevron del botón de colapso rota 180°.
- `.sidebar-link`:
  - Default: `color: var(--text-secondary)`, padding `10px 12px`, `border-radius: 6px`.
  - Hover: `background: var(--neon-subtle)`, `color: var(--text)`.
  - Activo: `.sidebar-link-active` → `background: var(--neon-subtle)`, `color: var(--neon-text)`.
- **Iconos de sidebar**: `font-size: 20px`, contenedor 36×36. Es la única excepción al tope de 20px en la escala tipográfica.

En mobile (≤640px) la sidebar se convierte en **drawer off-canvas**: `position: fixed`, `transform: translateX(-100%)` por defecto, `translateX(0)` cuando `data-sidebar="expanded"`. Ver `09-mobile.md`.

## 4.4 · Main y cards

```css
main {
    flex: 1;
    padding: 24px 24px 72px;
    overflow-y: auto;
    min-width: 0;
}
.card {
    background: var(--bg-surface);
    padding: 24px;
    border-radius: 8px;
    border: 1px solid var(--border);
}
```

- Main tiene padding asimétrico: 24px arriba/lados, **72px abajo** para que el contenido no choque con el toolbar flotante (`.view-toolbar`) que vive en `bottom: 24px`.
- Cards: fondo de superficie, padding 24px, radio 8px, borde 1px. **Sin sombra.** La única "elevación" es el contraste de color entre `--bg` (página) y `--bg-surface` (card).
- En mobile (≤640px) main va a `padding: 8px 0 72px` y card a `padding: 14px 12px` (en `≤1024px`) para maximizar ancho útil.

### Title del card (firma visual)

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
}
```

**El `//` naranja es una firma de la app.** Aparece en cada `h2` de card y también en `.cell-modal-header h4`. Es una referencia deliberada a los comentarios de código — refuerza el registro "terminal técnico". Si creas un heading nuevo fuera de `.card`, considera añadir el `::before` con `//` cuando encaje semánticamente.

### Secciones dentro de cards

```css
.card-section {
    padding-bottom: 24px;
    margin-bottom: 24px;
    border-bottom: 1px solid var(--border);
}
.card-section-last {
    /* sin border-bottom */
}
```

Usado en Settings para dividir una card larga en bloques lógicos (columnas, cache, DB config, reports, etc.).

## 4.5 · Breakpoints

| Breakpoint | Propósito | Archivos |
|---|---|---|
| `≤480px` | Ajuste extremo para mobile pequeño (poco uso) | settings, login |
| `≤640px` | **Mobile** — drawer sidebar, main sin padding lateral, reduce font sizes | Todo |
| `641-900px` | Tablet portrait, algunos ajustes de layout específicos | settings, charts |
| `≤768px` | Mid-mobile / phone landscape; mayoritariamente para logic-view y modals | logic-view, modal-label |
| `901-1024px` | Tablet landscape, sidebar autocolapsada | Sidebar |
| `≤1024px` | Sidebar pasa a modo colapsado automático | General |
| `≤1100px` | Charts: ajuste de grid | charts |
| `≤1300px` | Settings: grid de columnas pasa a stack | settings |

Breakpoints declarados: `480`, `640`, `720`, `768`, `900`, `901`, `1024`, `1100`, `1300`, `1600`. **No introduzcas breakpoints nuevos** sin una razón documentada.

### Safe-area insets (iOS)

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
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }
    }
}
```

El `max(…)` en desktop asegura que no bajemos del padding base (24px) incluso si el inset es mayor. En mobile aplicamos el inset raw porque el padding base es 0.

## 4.6 · Max-widths clave

| Elemento | Max-width | Contexto |
|---|---|---|
| `.cell-tooltip` | `420px` | Tooltip de celda |
| `.cell-modal` | `600px` | Modal de valor de celda |
| `.modal-box` (estándar) | `480px` | Modales genéricos (filter condition, CSV options, etc.) |
| `.csv-modal-box` | `460px` | CSV modal |
| `.cache-size-modal-box` | `420px` | Cache size modal |
| `.perf-modal-box` | `560px` | DB perf modal |
| `.history-matrix-box` | `1600px` (95vw) | History matrix (overlay ancho) |
| `.login-card` | `380px` | Login |
| `.parts-popover` | `420px` | Popover de parts |
| `.cbar-popover` | `280px` | Popover de columnas |

## 4.7 · Z-index scale

| Capa | Valor | Uso |
|---|---|---|
| Base del sidebar | `95` | Off-canvas drawer mobile |
| Header | `100` | Sticky top bar |
| Table fade indicators | `2` | Gradientes laterales de scroll |
| Sticky table headers | `1-3` | `th` en scroll horizontal |
| Logic minimap | `119-120` | Botón + minimap |
| Logic tooltip | `9999` | Tooltip sobre todo |
| Cell modal / popovers simples | `1050-1100` | Modal de celda, tooltip flotante |
| View toolbar | `900` | Toolbar flotante abajo |
| Modal overlay | `300` | Modales estándar |
| Dropdown menu | `200` | Language dropdown, ws-dropdown |
| Toasts | `9999` | Flash toasts |

No introduzcas valores nuevos sin revisar esta escala — los colapsos de z-index son fuente de bugs clásicos.
