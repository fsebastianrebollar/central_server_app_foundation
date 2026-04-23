# 05 · Paletas de color

## 5.1 · Principio rector

**Un solo color de marca** (`--neon: #ff6a00`) que concentra toda la atención. El resto son neutros (grises tonales) + verdes/rojos semánticos + una paleta específica para charts que se extiende en el eje "amarillo→rosa→cian" manteniendo la energía neón.

Si te encuentras introduciendo un color acento distinto al naranja (por ejemplo un violeta "para variar"), probablemente estés diseñando fuera del sistema — retrocede.

## 5.2 · Escala de grises

Definida implícitamente a través de las variables (ver `02-theme-tokens.md`):

| Nivel | Claro | Oscuro |
|---|---|---|
| Fondo página | `#f4f3f0` | `#0a0a0f` |
| Fondo superficie | `#fdfcfa` | `#141419` |
| Fondo input | `#f7f6f3` | `#1a1a20` |
| Fondo `th` (solo dark) | `var(--input-bg)` | `#1f1f26` |
| Border default | `#e6e4e1` | `#2e2e34` |
| Border hover | `#c8c5c1` | `#46464d` |
| Texto secundario | `#85858d` | `#8a8a94` |
| Texto primario | `#2c2c30` | `#e4e4e7` |

En claro los grises tiran a cálido (amarillento), no son neutros absolutos — intencional para suavizar la lectura prolongada. En oscuro son prácticamente neutros con ligero azulado.

## 5.3 · Estados semánticos

### OK / éxito

```
--success-bg     = #eaf6ee  /  #052e16   (badge background)
--success-text   = #1a6b4a  /  #86efac   (badge text, row indicator, dot)
--success-border = #bfe8cd  /  #14532d   (badge border)
```

Adicionalmente, los **bordes izquierdos** de filas OK en tablas usan verde hardcoded:

```css
.row-ok { border-left: 5px solid #16a34a; }
```

Y en logic-view:

```css
.logic-step-card-ok { border-left: 3px solid var(--success-border); }
```

### FAIL / error

```
--error-bg     = #fdf1f1  /  #450a0a
--error-text   = #9e2a2a  /  #fca5a5
--error-border = #f5d0d0  /  #7f1d1d
```

Y el indicador de fila:

```css
.row-fail { border-left: 5px solid #dc2626; }
.logic-step-card-fail { border-left: 3px solid var(--error-border); }
```

### Regla: nunca uses rojo/verde para decoración

Rojo y verde en esta app **significan algo**. Si necesitas un estado neutro, usa `.badge-other`:

```css
.badge-other {
    background: var(--input-bg);
    color: var(--text-secondary);
    border: 1px solid var(--border);
}
```

## 5.4 · Acento neón

El token `--neon` aparece en estos contextos, y en ningún otro:

| Contexto | Cómo aparece |
|---|---|
| Logo brand | Fondo sólido, texto negro, glow |
| Botón primario (`.login-btn`, `.ws-modal-btn-primary`) | Fondo sólido, texto blanco |
| `.fbar-apply`, `.pagination-btn-active`, `.view-toolbar-btn-active` | Fondo sólido, texto blanco |
| `.test-history-fullbtn:hover` | Fondo sólido al hacer hover, texto negro |
| Focus / active | Border 1px + glow |
| Filter preset activo, radio/checkbox activo | Border 1px + glow |
| `//` decorativo (`.card h2::before`, `.cell-modal-header h4::before`) | Texto sólido |
| Hover sutil (`.sidebar-link:hover`, `.clickable-row:hover`, `.fbar-pill:hover`) | Background `--neon-subtle` |

**Hay una sutileza con el color del texto sobre fondo neón**: por defecto se usa `#fff` (blanco). La excepción es el `.app-header-logo` que usa `#000` (negro) porque el texto del logo es muy pequeño y necesita el máximo contraste. Si creas un botón primario nuevo, **usa `#fff`**.

## 5.5 · Acento neón azul (secundario)

Se reserva para:

- **Badges "parallel"** en logic view:
  ```css
  .logic-step-badge-parallel {
      background: rgba(0, 160, 255, 0.12);
      color: var(--neon-blue);
      border: 1px solid rgba(0, 160, 255, 0.3);
  }
  ```
- **Filter date input focus**:
  ```css
  .fbar-date:focus { border-color: var(--neon-blue); }
  ```
  (Excepción deliberada: los rangos temporales son el tipo de filtro más frecuente y distinguirlos con azul ayuda a leerlos rápido entre pills naranjas.)
- **Segunda serie** en charts de línea cuando hay dos (`stroke: PALETTE[2]` o similar).

No lo introduzcas en otros contextos.

## 5.6 · Paleta de charts

Definida en `app/static/js/charts.js`:

```js
var PALETTE = [
    '#ff6a00',  // neon orange (app accent)
    '#ffd60a',  // neon yellow
    '#ff006e',  // neon pink
    '#00e5ff',  // neon cyan
    '#ff9f1c',  // amber
    '#b5ff00',  // neon lime
    '#fb5607',  // flame
    '#f72585',  // magenta
    '#ffbe0b',  // saffron
    '#06ffa5',  // mint
    '#ff4500',  // deep orange
    '#c77dff',  // violet
    '#ff8500',  // tangerine
    '#ffee32',  // bright yellow
    '#ff3c38'   // coral
];
```

- Naranja siempre es `PALETTE[0]` (la primera serie del chart lleva el color de marca).
- El resto siguen un arco warm → hot → cyan → neutral — elegidos para que slices adyacentes sean visualmente distinguibles.
- **Regla**: si añades un chart nuevo, recicla esta paleta. **No la amplíes**. Si tienes >15 series, la visualización es el problema, no los colores.

## 5.7 · Paleta de branches (Gantt + Logic)

Se asigna por JS a través de la custom property `--bc` (Gantt) o `--branch-color` (Logic):

```css
.gantt-bc { background: var(--bc); color: #fff; }
```

El valor de `--bc` se setea inline desde JS picking from a 6-8 color rotation alineada con la paleta de charts (orange, pink, cyan, yellow, magenta, mint). Ver `app/static/js/logic-view.js` y `app/templates/steps.html` (inline Gantt).

**Coherencia cross-vista**: la misma branch debe tener el mismo color en Gantt, Logic y minimap. Se logra ordenando las branches por primer timestamp (o alfabéticamente como secondary key) antes de asignar índice a la paleta.

## 5.8 · Cuándo `color-mix()` es aceptable

Las versiones atenuadas de un color de branch o del `--pipeline` se hacen con `color-mix()`:

```css
background: color-mix(in srgb, var(--branch-color) 15%, transparent);
border: 1px solid color-mix(in srgb, var(--branch-color) 40%, transparent);
```

Esto solo se usa cuando el color base proviene de una variable inline dinámica (una branch). Para los tokens canónicos ya existen variantes `--neon-subtle`, `--neon-glow`, etc., así que **no reemplaces `var(--neon-subtle)` por `color-mix(in srgb, var(--neon) 7%, transparent)`**.

## 5.9 · Ejemplo: elegir color para algo nuevo

Te piden un "tag de prioridad" con tres niveles (alta, media, baja):

- **Alta** → usa el patrón `--error-*` (es urgencia, semánticamente rojo).
- **Media** → `.badge-other` (neutro).
- **Baja** → `.badge-other` también — o, si hace falta distinción, `var(--text-secondary)` como color de texto con fondo `--input-bg`.

**NO** inventes un "amarillo de advertencia" nuevo. Si el producto lo necesita de verdad, abre la conversación explícitamente antes.
