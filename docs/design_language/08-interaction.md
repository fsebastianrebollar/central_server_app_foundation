# 08 · Interacción

Hover, focus, transiciones y animaciones. La app es densa y usa micro-feedback constante para que el usuario perciba la interactividad sin overflow visual.

## 8.1 · Transiciones: la regla de los 0.15-0.2s

Hay dos tiempos canónicos:

| Duración | Función | Uso |
|---|---|---|
| `0.15s` | Micro-ajustes (color/borde) | `.btn-*`, `input`, `select`, `.sidebar-link` |
| `0.2s` | Movimiento (layout, sidebar, drawer) | `.sidebar { width }`, `.fbar-pill { transform }` |
| `0.22s` | Drawer off-canvas | `.sidebar { transform }` (mobile) |
| `0.35s` | Fade-out de toasts | `.flash-toast-hide` |

Regla: **nunca > 0.35s**. Si sientes que lo necesitas, probablemente es una animación de entrada (no una transición de estado) y debe ser un `@keyframes` corto.

## 8.2 · Patrón "transition: all 0.2s"

Muchos botones usan `transition: all 0.2s` porque cambian varias propiedades al hover (border, color, box-shadow):

```css
.btn-back {
    transition: all 0.2s;
}
.btn-back:hover {
    border-color: var(--neon);
    color: var(--neon-text);
    box-shadow: 0 0 8px var(--neon-subtle);
}
```

Sí, `all` es más costoso que listar propiedades individuales. En la práctica **no es un problema medible** porque son botones pequeños con pocos estados. No optimizar prematuramente.

## 8.3 · Hover: tres patrones canónicos

### Patrón A · "Neón full" (botones outline, controles redondos del header)

Al pasar el ratón, **border + color + glow cambian simultáneamente al neón**:

```css
.btn-back:hover {
    border-color: var(--neon);
    color: var(--neon-text);
    box-shadow: 0 0 8px var(--neon-subtle);
}
```

Usado en: `.btn-back`, `.btn-lang`, `.theme-toggle`, `.fbar-reset`, `.view-toolbar-btn`, `.cbar-pill`.

### Patrón B · "Background sutil" (filas, links, items de lista)

No cambia border ni color, solo background:

```css
.sidebar-link:hover {
    background: var(--neon-subtle);
    color: var(--text);
}
.clickable-row:hover {
    background: var(--neon-subtle);
}
```

Usado en: `.sidebar-link`, `.clickable-row`, `.fbar-pill:hover`, items de dropdown.

### Patrón C · "Opacity lift" (primary buttons)

El botón primario NO cambia de color — baja opacity:

```css
.login-btn:hover,
.ws-modal-btn-primary:hover {
    opacity: 0.85;
}
```

La razón: cambiar `--neon` a otro naranja al hover rompería la firma. Atenuar es más honesto.

## 8.4 · Focus

### `:focus` default

La mayoría de inputs y botones fijan `outline: none` al reset y reintroducen el focus a través de `border-color: var(--neon)` + `box-shadow` neón:

```css
select:focus {
    border-color: var(--neon);
    box-shadow: 0 0 0 3px var(--neon-subtle);
}
```

### `:focus-visible` (accesibilidad)

**Cuando el control es custom (checkbox/radio visual, card clicable)** y el focus default no se ve, añadimos `:focus-visible`:

```css
input[type="checkbox"]:focus-visible {
    outline: 2px solid rgba(255, 106, 0, 0.4);
    outline-offset: 2px;
}

.ws-card:focus-visible {
    outline: 2px solid var(--neon);
    outline-offset: 2px;
}
```

**Regla**: nunca hacer `:focus { outline: none; }` sin poner algo equivalente en `:focus-visible`. Un usuario con teclado debe saber dónde está.

## 8.5 · Active (clic)

Patrón muy discreto — casi no lo usamos. Los botones primarios reducen opacity ligeramente más (`opacity: 0.75`) en `:active`, pero muchos no tienen estado active explícito. El click se percibe por el cambio de ruta / modal abierto / dato refrescado.

Excepciones con `:active` notables:
- `.pagination-btn:active` — escala ligeramente.
- `.view-toolbar-btn:active` — intensifica el glow.

## 8.6 · Disabled

```css
.btn-*:disabled,
input:disabled,
select:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}
```

Las variantes custom (`input[type="checkbox"]:disabled`) usan `opacity: 0.45` (un pelo más atenuado para que no se lea como "interactivo al hover"). Nunca pintes el disabled con un color distinto — solo opacity + cursor.

## 8.7 · Animaciones `@keyframes`

La app tiene ~25 animaciones. Caen en tres categorías:

### Categoría A · **Entrada suave** (elementos que aparecen)

```css
@keyframes flash-toast-in {
    from { opacity: 0; transform: translateY(-12px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fbar-pill-in {
    from { opacity: 0; transform: scale(0.85); }
    to   { opacity: 1; transform: scale(1); }
}

@keyframes report-picker-in {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
}
```

Duración típica `0.2-0.3s`, `cubic-bezier(0.4, 0, 0.2, 1)` o `ease`. Nunca > `0.35s`.

### Categoría B · **Enfatizar cambio de estado** (pulsos, dirty marks)

```css
@keyframes fbar-apply-pulse {
    0%   { box-shadow: 0 0 0 0 var(--neon-glow); }
    70%  { box-shadow: 0 0 0 6px transparent; }
    100% { box-shadow: 0 0 0 0 transparent; }
}

@keyframes fbar-dirty-in {
    from { opacity: 0; transform: scale(0); }
    to   { opacity: 1; transform: scale(1); }
}
```

Un pulso de `0.6-1s` para señalar "aquí pasó algo". Se reproduce **una vez** — no en bucle. Bucles = ansiedad.

### Categoría C · **Animaciones ambientales de los reports**

Ver `9076-9800` de `style.css`: KPIs que crecen, barras que suben, spark lines que se dibujan, cards que drift lento. Todas gated por `IntersectionObserver` + `.in-view` para que solo animen al entrar en viewport. **Respetan `prefers-reduced-motion`** (ver `10-a11y.md`).

## 8.8 · Glow: cuándo y cómo

El glow (`box-shadow` neón sutil) es la firma más reconocible. Tres escalas:

| Escala | `box-shadow` | Contexto |
|---|---|---|
| **Tenue** | `0 0 8px var(--neon-subtle)` | Hover de botones outline pequeños |
| **Media** | `0 0 10px var(--neon-glow)` | Logo del header, focus de controles |
| **Intensa** | `0 0 10px var(--neon), 0 0 18px var(--neon-glow)` | Estado activo (sidebar-link-active, filter preset activo, chip chart) |

Regla: **nunca mezcles más de dos glows en un mismo elemento**. Si un botón activo ya tiene glow + pulse, no añadas una tercera sombra.

## 8.9 · Spin (loaders)

Dos spins canónicos, mismo valor:

```css
@keyframes loading-spin {
    to { transform: rotate(360deg); }
}
@keyframes perf-spin {
    to { transform: rotate(360deg); }
}
```

Ambos duran `1s` lineal y aplican a un `border-radius: 50%` con borde neón sobre el lado superior. **Si necesitas un tercer spinner**, reusa `loading-spin` — no crees uno nuevo.

## 8.10 · Preload guard

Al inicio del CSS:

```css
html.preload,
html.preload *,
html.preload *::before,
html.preload *::after {
    transition: none !important;
    animation-duration: 0s !important;
    animation-delay: 0s !important;
}
```

`base.html` añade `class="preload"` inline en `<head>` y lo quita tras `window.load`. Esto evita que el sidebar se "anime desde colapsado" al cargar una página con `data-sidebar="expanded"`. **No lo quites.** El flash del primer paint es uno de los bugs clásicos si se elimina.

## 8.11 · Cursor

- Botones y links: `cursor: pointer` (explícito, no confiar en defaults).
- Inputs y textareas: default (el navegador pone `text` donde toca).
- Disabled: `cursor: not-allowed`.
- Zonas de arrastre (drag-reorder de pills, zoom del Gantt axis): `cursor: grab` / `grabbing` al drag.
- **No usamos `cursor: help`** — preferimos tooltip via hover.

## 8.12 · Resumen de qué reacciona a qué

| Evento | Respuesta |
|---|---|
| Hover botón outline | Border + color + glow → neón |
| Hover fila tabla | Background → `--table-hover` |
| Hover link sidebar | Background → `--neon-subtle` |
| Focus input | Border → `--neon` + `box-shadow 3px --neon-subtle` |
| Focus custom control | `outline: 2px solid rgba(255,106,0,0.4)` con `outline-offset: 2px` |
| Click primary btn | `opacity: 0.85` |
| Click destructive | No hay feedback visual; el modal de confirmación ya es el feedback |
| Drag start | `cursor: grabbing`, elemento `opacity: 0.6` |
| Drop | Snap con transición `0.2s` |
| Toast aparece | `flash-toast-in 0.25s ease` |
| Toast desaparece | `flash-toast-hide 0.35s ease` |
