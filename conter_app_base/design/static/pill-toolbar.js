/* Conter floating pill toolbar — view/mode switcher component.
 *
 * Used for "view selectors" that sit at the bottom of a page and let
 * the user flip between modes (Tests/Joined/Steps, Table/Logic/Time,
 * product A/B/C in a report). Visually: a translucent pill strip,
 * one button per mode, with the active one highlighted.
 *
 * Usage:
 *
 *   const toolbar = PillToolbar.create({
 *       mount: "#my-toolbar-pill",             // element or selector
 *       items: [
 *           {value: "table", label: "Table", icon: "&#9776;"},
 *           {value: "logic", label: "Logic", icon: "&#9881;"},
 *           {value: "time",  label: "Time",  icon: "&#9201;"},
 *       ],
 *       value: "table",                         // initial active value
 *       onChange: (v) => {                      // fires on click
 *           render(v);
 *       },
 *       // Optional persistence layers (pick at most one):
 *       urlParam: "product",   // round-trips via ?product=<value>
 *       storageKey: "my.view", // round-trips via localStorage
 *       hashKey: "mode",       // round-trips via location.hash (#mode=<value>)
 *   });
 *
 * Instance methods:
 *   toolbar.setValue(v)    — activate `v` without firing onChange
 *   toolbar.setItems(list) — rebuild buttons (e.g. dynamic product list)
 *   toolbar.setVisible(ok) — show/hide the toolbar without unmounting
 *   toolbar.destroy()      — remove listeners + empty the mount
 *
 * The CSS classes (.view-toolbar-*) are owned by pill-toolbar.css,
 * which apps opt into by loading it from /design-static/pill-toolbar.css.
 */
(function (global) {
    "use strict";

    function $(sel) {
        if (!sel) return null;
        if (typeof sel !== "string") return sel;
        return document.querySelector(sel);
    }

    function _readInitial(opts) {
        // Priority: URL param > hash > localStorage. Apps that want a
        // hard-coded initial value should just pass `value:` and omit
        // the persistence hooks, matching classic static toolbars.
        try {
            if (opts.urlParam) {
                const u = new URLSearchParams(window.location.search);
                const v = u.get(opts.urlParam);
                if (v != null && v !== "") return v;
            }
            if (opts.hashKey) {
                const h = _parseHash(opts.hashKey);
                if (h != null) return h;
            }
            if (opts.storageKey) {
                const v = localStorage.getItem(opts.storageKey);
                if (v != null) return v;
            }
        } catch (_) {
            // Private mode can throw on localStorage. Fall through.
        }
        return opts.value != null ? opts.value : null;
    }

    function _parseHash(key) {
        // Supports both "#<value>" (single-key mode) and "#k=v&other=…".
        const h = (window.location.hash || "").replace(/^#/, "");
        if (!h) return null;
        if (h.indexOf("=") < 0) return h;
        const parts = h.split("&");
        for (let i = 0; i < parts.length; i++) {
            const [k, v] = parts[i].split("=");
            if (k === key) return decodeURIComponent(v || "");
        }
        return null;
    }

    function _persist(opts, value) {
        try {
            if (opts.urlParam) {
                const u = new URL(window.location.href);
                if (value != null && value !== "") {
                    u.searchParams.set(opts.urlParam, value);
                } else {
                    u.searchParams.delete(opts.urlParam);
                }
                window.history.replaceState(null, "", u);
            }
            if (opts.hashKey) {
                // Replace only our key; leave sibling keys intact.
                const h = (window.location.hash || "").replace(/^#/, "");
                const parts = h ? h.split("&") : [];
                const out = [];
                let replaced = false;
                for (let i = 0; i < parts.length; i++) {
                    const [k] = parts[i].split("=");
                    if (k === opts.hashKey) {
                        out.push(opts.hashKey + "=" + encodeURIComponent(value));
                        replaced = true;
                    } else if (parts[i].indexOf("=") < 0 && parts.length === 1) {
                        // Single legacy "#value" form → convert to k=v
                        out.push(opts.hashKey + "=" + encodeURIComponent(value));
                        replaced = true;
                    } else {
                        out.push(parts[i]);
                    }
                }
                if (!replaced) {
                    out.push(opts.hashKey + "=" + encodeURIComponent(value));
                }
                window.location.hash = out.join("&");
            }
            if (opts.storageKey) {
                localStorage.setItem(opts.storageKey, value);
            }
        } catch (_) {
            /* swallow — persistence is best-effort */
        }
    }

    function _makeButton(item) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "view-toolbar-btn";
        b.dataset.value = item.value;
        if (item.title) b.title = item.title;
        let html = "";
        if (item.icon) {
            html += '<span class="view-toolbar-icon">' + item.icon + "</span>";
        }
        if (item.label != null) {
            html += '<span class="view-toolbar-label">' + item.label + "</span>";
        }
        b.innerHTML = html;
        return b;
    }

    function create(opts) {
        if (!opts || !opts.mount) {
            throw new Error("PillToolbar.create: `mount` is required");
        }
        const mount = $(opts.mount);
        if (!mount) {
            throw new Error("PillToolbar.create: mount not found");
        }

        const state = {
            items: Array.isArray(opts.items) ? opts.items.slice() : [],
            value: null,
            onChange: typeof opts.onChange === "function" ? opts.onChange : null,
            opts: opts,
        };

        function _highlight() {
            mount.querySelectorAll(".view-toolbar-btn").forEach(function (b) {
                b.classList.toggle(
                    "view-toolbar-btn-active",
                    b.dataset.value === state.value
                );
            });
        }

        function _render() {
            mount.innerHTML = "";
            state.items.forEach(function (it) {
                const b = _makeButton(it);
                b.addEventListener("click", function () {
                    if (state.value === it.value) return;
                    state.value = it.value;
                    _highlight();
                    _persist(opts, it.value);
                    if (state.onChange) {
                        try { state.onChange(it.value); } catch (e) {
                            /* app handler errors shouldn't break the toolbar */
                            console.error(e);
                        }
                    }
                });
                mount.appendChild(b);
            });
            _highlight();
        }

        // Initial value resolution + first render.
        const initial = _readInitial(opts);
        const known = state.items.map(function (i) { return i.value; });
        state.value = known.indexOf(initial) >= 0
            ? initial
            : (state.items[0] && state.items[0].value) || null;
        _render();

        // Hash listener (optional) — keeps the toolbar in sync if another
        // actor (e.g. another widget or the back button) rewrites the hash.
        let _hashHandler = null;
        if (opts.hashKey) {
            _hashHandler = function () {
                const h = _parseHash(opts.hashKey);
                if (h != null && h !== state.value && known.indexOf(h) >= 0) {
                    state.value = h;
                    _highlight();
                    if (state.onChange) state.onChange(h);
                }
            };
            window.addEventListener("hashchange", _hashHandler);
        }

        return {
            setValue: function (v) {
                if (v === state.value) return;
                if (known.indexOf(v) < 0) return;
                state.value = v;
                _highlight();
                _persist(opts, v);
            },
            getValue: function () { return state.value; },
            setItems: function (items) {
                state.items = Array.isArray(items) ? items.slice() : [];
                const ks = state.items.map(function (i) { return i.value; });
                if (ks.indexOf(state.value) < 0) {
                    state.value = ks[0] || null;
                }
                _render();
                _persist(opts, state.value);
            },
            setVisible: function (visible) {
                const wrap = mount.closest(".view-toolbar") || mount;
                wrap.style.display = visible ? "" : "none";
            },
            destroy: function () {
                if (_hashHandler) {
                    window.removeEventListener("hashchange", _hashHandler);
                }
                mount.innerHTML = "";
            },
        };
    }

    global.PillToolbar = { create: create };
})(typeof window !== "undefined" ? window : this);
