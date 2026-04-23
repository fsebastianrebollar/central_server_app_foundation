# Design Language — central_server_app_foundation

Guía canónica del lenguaje visual del chassis. Es la fuente única de verdad para decisiones de diseño: colores, tipografía, componentes, espaciados, modos claro y oscuro.

El CSS canónico vive en `central_server_app_foundation/design/static/style.css` (este repo). Las apps que extienden el chassis lo cargan automáticamente a través de `base.html` y añaden sus propios estilos en el bloque `app_styles`.

> Si editas `style.css` y el cambio afecta alguna sección de esta guía, actualiza ambos en el mismo commit. Si el cambio introduce un patrón nuevo, añade la sección correspondiente.

## Índice

1. [Filosofía y principios](01-philosophy.md) — qué define el look & feel, qué está prohibido.
2. [Tokens y theming](02-theme-tokens.md) — variables CSS, modo claro/oscuro, sombras, overlays.
3. [Tipografía](03-typography.md) — stack monospace, escala de tamaños, pesos.
4. [Layout](04-layout.md) — header, sidebar, main, breakpoints, cards.
5. [Paletas de color](05-colors.md) — acento neón, estados (ok/fail), charts, branches.
6. [Componentes](06-components.md) — botones, tablas, modales, badges, pills, paginación, toolbar flotante, workspace widget, toasts, tooltips.
7. [Formularios](07-forms.md) — inputs, selects, checkboxes tipo switch, radios, textarea.
8. [Interacción](08-interaction.md) — hover, focus, transiciones, animaciones, glow neón.
9. [Responsive / mobile](09-mobile.md) — breakpoints `≤640`, `≤1024`, safe-area, drawer.
10. [Accesibilidad y motion](10-a11y.md) — contraste, `prefers-reduced-motion`, focus visible.
11. [Anti-patrones](11-anti-patterns.md) — lo que NUNCA se hace.

## Snippets CSS listos para copiar

Los archivos de `snippets/` son extractos aislados del `style.css` actual. Son **referencia canónica**: si construyes un componente nuevo, arráncalo desde el snippet correspondiente.

| Snippet | Contiene |
|---|---|
| [`snippets/tokens.css`](snippets/tokens.css) | `:root` y `[data-theme="dark"]` con todas las variables. |
| [`snippets/typography.css`](snippets/typography.css) | Body, `.mono`, escala de títulos. |
| [`snippets/buttons.css`](snippets/buttons.css) | Patrones `.btn-*`, `.login-btn`, `.btn-danger`, `.btn-back`. |
| [`snippets/cards.css`](snippets/cards.css) | `.card`, `.card h2`, `.card-section`. |
| [`snippets/tables.css`](snippets/tables.css) | `table`, `th.sortable`, fades laterales, row-ok/fail. |
| [`snippets/badges.css`](snippets/badges.css) | `.badge-ok`, `.badge-fail`, `.badge-other`. |
| [`snippets/pills.css`](snippets/pills.css) | `.view-toolbar-pill` (chassis) — apps añaden sus propias pill variants. |
| [`snippets/modals.css`](snippets/modals.css) | `.modal-overlay`, `.modal-box`, header/body/footer. |
| [`snippets/inputs.css`](snippets/inputs.css) | `input`, `select`, checkbox switch, radio neón, textarea. |

## Cómo usar esta guía

- **Antes de crear un componente nuevo**: busca en `06-components.md` si ya existe uno equivalente y reutilízalo.
- **Antes de hardcodear un color**: búscalo en `02-theme-tokens.md`; si no existe, añade la variable en `:root` **y** `[data-theme="dark"]`.
- **Antes de añadir una clase nueva al CSS**: valida contra `11-anti-patterns.md`.
- **Antes de tocar un `@media`**: revisa `09-mobile.md` — los breakpoints son fijos (`640`, `768`, `1024`).
