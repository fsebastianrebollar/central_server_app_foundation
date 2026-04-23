# 01 · Filosofía y principios

## El look & feel en una frase

> **Terminal técnico con acento neón naranja**: densidad alta de datos, tipografía monospace, superficies planas con bordes finos, un único color de marca (`--neon: #ff6a00`) que concentra toda la atención, y modo oscuro como estado natural.

## Los seis principios

### 1. Dark-first, pero bi-tonal real

El tema por defecto es oscuro. Existe un modo claro completo, no un "afterthought": ambos se derivan de las mismas variables CSS. Un `<script>` inline en `<head>` aplica `data-theme` **antes del primer paint** para evitar el flash blanco.

### 2. Monospace en toda la UI

Stack: `"SF Mono", "Fira Code", "Consolas", "JetBrains Mono", monospace`. Jamás sans-serif. Esto es una app técnica que muestra IDs, timestamps y resultados — la tipografía refuerza el registro.

### 3. Flat + borde

Las superficies son `var(--bg-surface)` con `1px solid var(--border)` y `border-radius: 8px`. **No se usan sombras para dar elevación a cards**; las sombras existen solo para modales, popovers y elementos flotantes (ver `--shadow-popup`, `--shadow-modal`).

### 4. Un único acento

`--neon: #ff6a00` es el único color de marca. Existe `--neon-blue` para secundarios muy puntuales (charts, estado "parallel"), pero si te encuentras añadiendo un tercer acento, estás fuera del sistema — repiensa el diseño.

### 5. El glow es firma, no decoración

El resplandor naranja aparece en:
- Logo del header (`box-shadow: 0 0 10px var(--neon-glow)`).
- Hover de botones / toggles (`box-shadow: 0 0 8px var(--neon-subtle)`).
- Switch activado, radio checked, focus visible.
- Modal (`box-shadow: 0 8px 40px var(--modal-shadow), 0 0 12px var(--neon-glow)`).

Es sutil — `--neon-glow` en claro es `rgba(255,106,0,0.18)`, en oscuro `0.4`. No se usa en texto corrido ni en estados neutros.

### 6. Densidad sobre respiración

Esta es una app de tablas y filtros. Padding compacto (10-14 px en tablas, 16-24 px en cards), font-size pequeño (12-14 px en general), ningún heading por encima de 20 px salvo el `.dashboard-hero`. Cuando dudes entre más aire y más datos, gana datos.

## Restricciones estructurales heredadas

Estas no son decisiones de diseño — son invariantes que el diseño respeta:

- **Sin frameworks CSS** (nada de Bootstrap, Tailwind, Bulma). Vanilla CSS.
- **Sin frameworks JS** (nada de React, Vue, jQuery). Vanilla JS.
- **Sin preprocesador** (nada de Sass, Less). CSS moderno plano, con custom properties.
- **Un único archivo grande** `style.css` (~10 400 LOC) + `logic-view.css` (~530 LOC) para el Logic view.

Si alguna vez rompes alguna de estas, no es un cambio de diseño sino de arquitectura — discútelo antes.

## Cómo decidir si algo encaja

Pregúntate, en este orden:

1. **¿Puedo hacerlo con una variable existente?** Si sí, hazlo así. Si no, ¿añado variable nueva o reutilizo semánticamente una que ya tenga el significado?
2. **¿Qué tamaño de texto pide la escala tipográfica?** (ver `03-typography.md`). No improvises tamaños.
3. **¿Necesita acento neón?** Solo si representa acción, selección activa o estado "en curso". Si es informativo neutro → `var(--text-secondary)`.
4. **¿Lleva sombra?** Solo si es flotante (modal, dropdown, toolbar). Todo lo anclado al flujo → bordes.
5. **¿Tiene equivalente mobile?** Revisa `09-mobile.md` antes de cerrar el diseño.
