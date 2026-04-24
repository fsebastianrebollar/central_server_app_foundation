/* Conter chassis runtime — theme toggle, sidebar drawer, ESC handler.
 *
 * App-specific UI (tables, filters, widgets, table sorting, cell-modal
 * JSON pretty-printing) stays in each app's own script bundle. This
 * file only owns the behavior that every app inherits verbatim from
 * the chassis template.
 *
 * Theme POST target is read from `window.APP_THEME_SAVE_URL` (injected
 * by base.html from `chassis_endpoints.theme_save`) — falls back to
 * "/api/theme" for back-compat.
 */
document.addEventListener('DOMContentLoaded', () => {
    // === Theme toggle ===
    const toggle = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-icon');
    const saved = localStorage.getItem('theme') || 'dark';
    const THEME_URL = window.APP_THEME_SAVE_URL || '/api/theme';

    function applyTheme(theme, save) {
        document.documentElement.setAttribute('data-theme', theme);
        if (icon) icon.innerHTML = theme === 'dark' ? '&#9788;' : '&#9790;';
        localStorage.setItem('theme', theme);
        if (save) {
            fetch(THEME_URL, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({theme: theme})
            });
        }
    }

    applyTheme(saved, false);

    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            applyTheme(current === 'dark' ? 'light' : 'dark', true);
        });
    }

    // === Sidebar toggle (desktop: persists; mobile: ephemeral overlay) ===
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const hamburger = document.getElementById('sidebar-hamburger');
    const backdrop = document.getElementById('sidebar-backdrop');
    const MOBILE_MQ = window.matchMedia('(max-width: 640px)');

    function setSidebar(state, persist) {
        document.documentElement.setAttribute('data-sidebar', state);
        if (persist && !MOBILE_MQ.matches) localStorage.setItem('sidebar', state);
    }

    function toggleSidebar() {
        const current = document.documentElement.getAttribute('data-sidebar');
        setSidebar(current === 'expanded' ? 'collapsed' : 'expanded', true);
    }

    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
    if (hamburger) hamburger.addEventListener('click', toggleSidebar);
    if (backdrop) backdrop.addEventListener('click', () => setSidebar('collapsed', false));

    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', () => {
            if (MOBILE_MQ.matches) setSidebar('collapsed', false);
        });
    });

    MOBILE_MQ.addEventListener('change', (e) => {
        if (!e.matches) {
            const persisted = localStorage.getItem('sidebar') || 'expanded';
            setSidebar(persisted, false);
        } else {
            setSidebar('collapsed', false);
        }
    });

    if (MOBILE_MQ.matches) setSidebar('collapsed', false);

    // === Language dropdown ===
    const langBtn = document.getElementById('btn-lang');
    const langMenu = document.getElementById('lang-dropdown-menu');
    if (langBtn && langMenu) {
        langBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            langMenu.classList.toggle('open');
        });
        document.addEventListener('click', () => langMenu.classList.remove('open'));
    }

    // ESC closes the mobile drawer and any open modal overlays.
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (MOBILE_MQ.matches &&
            document.documentElement.getAttribute('data-sidebar') === 'expanded') {
            setSidebar('collapsed', false);
            return;
        }
        const openModal = document.querySelector(
            '.cell-modal-overlay.cell-modal-open, .modal-overlay.modal-open, ' +
            '.app-modal-overlay.app-modal-open, .history-matrix-overlay.history-matrix-open'
        );
        if (openModal) {
            openModal.classList.remove(
                'cell-modal-open', 'modal-open', 'app-modal-open', 'history-matrix-open'
            );
        }
    });
});
