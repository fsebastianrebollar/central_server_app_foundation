# 11 · Anti-patrones

Lista explícita de lo que **no** se hace en Conter Stats. Cuando dudes, revisa aquí antes.

## 11.1 · CSS

### ❌ No hardcodees colores en componentes

```css
/* MAL */
.my-widget { background: #fdfcfa; border: 1px solid #e6e4e1; }

/* BIEN */
.my-widget { background: var(--bg-surface); border: 1px solid var(--border); }
```

**Por qué**: rompe el dark mode al instante. La única excepción documentada son los borders izquierdos OK/FAIL (`#16a34a` / `#dc2626`) y la chart PALETTE — colores semánticos inmutables.

### ❌ No introduzcas colores acento nuevos

```css
/* MAL — un "morado para variar" */
.premium-badge { background: #9333ea; color: #fff; }
```

Un solo acento (`--neon`). Un secundario puntual (`--neon-blue`) solo en sus 3 sitios permitidos. Si necesitas distinción, usa grises o una variante semántica existente.

### ❌ No `!important` salvo para resets obligatorios

El único `!important` aceptable es el del preload guard y el toast `z-index: 9999 !important` (compite con código de terceros). Si vas a añadir otro, justifica en comentario o reconsidera.

### ❌ No uses unidades mezcladas sin razón

```css
/* MAL */
padding: 10px 0.8em 12px 1rem;

/* BIEN */
padding: 10px 12px;
```

`px` para todo lo de layout, `em/rem` solo cuando quieres escala con tamaño de fuente (raro en esta app).

### ❌ No inventes breakpoints

Los breakpoints canónicos son `480`, `640`, `720`, `768`, `900`, `901`, `1024`, `1100`, `1300`, `1600`. Añadir un `915px` o `1200px` porque "en mi pantalla se ve raro" fragmenta el sistema. Ajusta max-widths de contenedores antes de añadir un media query.

### ❌ No uses sombras fuertes en modo claro

El `--shadow-card` claro usa alphas **0.03-0.12**. Si pones `0 4px 12px rgba(0,0,0,0.25)` en un card claro, se ve pesado y choca con el resto del tema. Usa las variables `--shadow-*`.

### ❌ No uses `transform: scale()` > 1.05 en hover

```css
/* MAL */
.btn:hover { transform: scale(1.15); }  /* "salta" */

/* BIEN */
.btn:hover { transform: scale(1.02); }  /* apenas perceptible, pro */
```

La app es densa; elementos que "crecen" en hover se sienten toys. Máximo scale 1.05, preferiblemente sin scale y solo color/border.

### ❌ No mezcles `.modal-open` con `.active`

El modal overlay se abre con `.modal-open`. **Solo** con `.modal-open`. Documented bug: al mezclar `.active` un modal (Cache Manager, Service Control) no abría.

```css
/* BIEN */
.modal-overlay.modal-open { display: flex; }

/* MAL — rompe el Cache Manager */
.modal-overlay.active { display: flex; }
```

### ❌ No uses `transition: all` en elementos grandes

Para botones y pills es aceptable (son elementos pequeños). Para un `.card` o un `.sidebar`, lista solo las propiedades que cambian: evitas reflows innecesarios.

```css
/* BIEN en .sidebar */
transition: width 0.2s, transform 0.22s ease;

/* MAL */
transition: all 0.2s;   /* en un elemento que cambia height, width, transform → jank */
```

## 11.2 · HTML y JS

### ❌ No escribas estilos inline salvo para valores dinámicos

```html
<!-- MAL: estilo estático inline -->
<div style="background: #fdfcfa; padding: 24px;">...</div>

<!-- BIEN: variable dinámica que solo JS conoce -->
<div class="branch-segment" style="--branch-color: #ff006e;">...</div>
```

Los `style="..."` aceptables son exclusivamente para custom properties dinámicas (`--branch-color`, `--bc`, `--pipeline`).

### ❌ No añadas frameworks JS

Prohibido: React, Vue, Svelte, jQuery, Alpine, htmx. **Vanilla only**. Es una decisión arquitectónica firme. Si te ves escribiendo mucho DOM manipulation, plantea un helper interno, no un framework.

### ❌ No añadas librerías CSS

Prohibido: Tailwind, Bootstrap, Bulma, etc. Los estilos viven en `style.css` y son el sistema. Una librería nueva añadiría tokens que conflictan y estilos que hay que pelear.

### ❌ No uses `innerHTML` con datos del servidor sin escapar

El backend ya escapa Jinja por default. Si construyes HTML en JS con datos del servidor, usa `textContent` o DOM API. `innerHTML` con interpolación string-concat es XSS-waiting.

### ❌ No introduzcas un `setInterval` global

Hay un scheduler de reports en backend. El frontend **no** debe pollear. Si necesitas refrescar algo, hazlo bajo demanda (click, modal abierto) o con WebSocket en un futuro lejano — nunca `setInterval(fetch, 5000)`.

## 11.3 · Diseño visual

### ❌ No uses `border-radius` > 10px para contenedores

Max `8px` para cards/modales, `6px` para botones/inputs, `4px` para flashes/badges, `50%` para controles redondos. Un card con `border-radius: 20px` se ve fuera del sistema.

### ❌ No uses texto < 9px

La escala llega a `9px` (badges de rol en sidebar). Por debajo no lee bien en monitores estándar ni en Retina al 100%.

### ❌ No uses texto > 20px salvo en `.dashboard-hero`

La app es densa. Los títulos grandes tipo "hero" solo caben en la landing del dashboard. Un `h1` de 32px en una modal está fuera del sistema.

### ❌ No uses gradientes como decoración

Los únicos gradientes aceptables son:
- El interior del checkbox switch cuando está `:checked` (efecto sutil de gloss).
- El glow radial del logo.
- Backgrounds de charts KPI (muy sutil, del brand color).

**No** gradientes de fondo en cards, modales, headers, botones. Planos o con glow.

### ❌ No uses sombras como única separación

Los cards se separan por **color de fondo** (`--bg-surface` vs `--bg`) + **borde 1px** (`--border`). La sombra es opcional. Un card con solo `box-shadow` y sin borde se ve flotante y sucio en modo claro.

### ❌ No uses emoji como icono

Los emojis (🔥 🚀 ✅) renderizan distinto en cada OS y en cada versión. La app usa caracteres Unicode específicos (`×`, `//`, `≡`, `✓`) y SVG inline. Nunca emoji.

### ❌ No disuelvas contenedores principales en mobile

```css
/* MAL — antes lo hacíamos y el usuario pidió revertirlo */
@media (max-width: 640px) {
    .card        { background: transparent; border: none; }
    .wiki-layout { background: transparent; border: none; }
}

/* BIEN — mismo tratamiento que desktop, padding lateral de `main` absorbe el aire */
@media (max-width: 640px) {
    main  { padding: 8px 10px 72px; }
    .card {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 14px 12px;
    }
}
```

**Por qué**: cuando la card pierde fondo y borde, el contenido se lee como "texto suelto sobre la página", no como panel. Pierdes la identidad del componente. El coste de restaurar es ~20px de ancho útil (10px padding × 2) — asumido por política. Aplica a `.card` y a `.wiki-layout` (los dos contenedores principales de la app).

## 11.4 · Estructura y arquitectura

### ❌ No crees un nuevo archivo CSS

Todo vive en `app/static/css/style.css` (y `logic-view.css` para la vista lógica). No introducir `settings.css`, `dashboard.css`, etc. La razón: **navegación simple** y **evita conflictos** de especificidad entre archivos.

### ❌ No añadas un `z-index` arbitrario

La escala está documentada en `04-layout.md` §4.7. Si necesitas un z nuevo, **revisa** antes de inventar:
- `95` drawer sidebar
- `100` header
- `200` dropdown
- `300` modal overlay
- `900` view toolbar
- `1050-1100` cell modal / tooltips simples
- `9999` toasts

Valor ad-hoc como `888` o `5000` crea bugs de apilamiento clásicos.

### ❌ No introduzcas caches nuevos sin seguir el patrón

Si añades un cache, sigue el patrón de `keys_cache` / `page_cache` / `chart_agg_cache`:
- Cache key incluye **todos** los filtros relevantes (incluido `_bench_ids`).
- Si es de paginación, incluye **hash de filtros**, no solo `(keys, columns)`. Ver nota en CLAUDE.md sobre `ds_key`.

### ❌ No cambies la estructura del header (52px)

La altura `52px` del header es un valor load-bearing: `calc(100vh - 52px)` en `.app-layout`, `top: 68px` en toasts, `top: 52px` en sidebar drawer. Cambiar esto rompe 4-5 capas simultáneamente.

### ❌ No mezcles inglés y español en copy

La UI va **en inglés** (i18n diferida; flask-babel lo soporta pero la app maestra es en inglés). Los docs (`CLAUDE.md`, `docs/`) van **en español**. No mezcles dentro de un mismo archivo.

## 11.5 · Workflow

### ❌ No hagas cambios de diseño sin screenshot en Telegram

El usuario trabaja remoto y revisa UI en móvil. Si tocas la UI, envía screenshot (`/screenshot <descripción>`). Pero **solo si el usuario lo pide** — nunca proactivamente.

### ❌ No olvides el CSS cross-theme

Cualquier cambio en `style.css` debe probarse en claro **y** oscuro. Si no quieres tocar ambos, probablemente no debas usar una variable nueva — existirá ya una que cubra ambos.

### ❌ No borres animaciones de reports sin gate

Las animaciones de reports tienen un costo al desarrollar pero son **firma del look**. Si una molesta, gate-ealas con `prefers-reduced-motion` o con `IntersectionObserver`. No las elimines.

### ❌ No uses "temporary" o "TODO" en nombres de clases

```css
/* MAL */
.tmp-button-fix { ... }

/* BIEN: dale el nombre definitivo desde el principio */
.btn-ghost { ... }
```

El CSS no se refactoriza a menudo. Lo "temporal" se queda.

## 11.6 · Resumen en 10 reglas

1. **Una sola fuente** de tokens (`:root` + `[data-theme="dark"]`).
2. **Un solo acento** de marca (`--neon`).
3. **Un solo stack** de fuente (monospace).
4. **Un solo archivo** principal de CSS (`style.css`).
5. **Breakpoints fijos** (`640`, `1024`, y sus satélites documentados).
6. **Ninguna librería** CSS ni JS framework.
7. **Ningún color hardcodeado** salvo los semánticos inmutables documentados.
8. **Ninguna animación > 0.35s** salvo las ambientales gated por `prefers-reduced-motion`.
9. **Ningún modal sin** `.modal-open`.
10. **Ningún PR de UI sin** probar claro + oscuro + mobile.
