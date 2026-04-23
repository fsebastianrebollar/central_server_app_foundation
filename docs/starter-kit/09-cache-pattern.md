# 09 · Cache in-process pattern

Patrón para caches en RAM (opcional: persistencia a disco) cuando tienes queries caras repetibles y **no quieres** una dependencia externa (Redis/Memcached).

## Cuándo aplicar

- Query costosa (>100ms) que se repite con los mismos inputs.
- Despliegue mono-proceso o pocos procesos sin coordinación.
- No necesitas compartir cache entre máquinas.

Si alguno de estos falla, usa Redis y no este patrón.

## Patrón básico — LRU en RAM

```python
# app/services/result_cache.py
from functools import lru_cache
from collections import OrderedDict
from typing import Any
import threading


class LRUCache:
    """Thread-safe LRU cache with optional max size."""

    def __init__(self, maxsize: int = 128):
        self._data: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any, default=None):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                self.hits += 1
                return self._data[key]
            self.misses += 1
            return default

    def set(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = value
            if len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def invalidate(self) -> None:
        with self._lock:
            self._data.clear()

    def stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._data),
                "hits":    self.hits,
                "misses":  self.misses,
                "maxsize": self._maxsize,
            }


# Module-level singleton
_cache = LRUCache(maxsize=256)


def fetch_data(filters: dict, sort: dict) -> list[dict]:
    # Normalize key: make dicts hashable and order-independent
    key = (
        tuple(sorted(filters.items())),
        tuple(sorted(sort.items())),
    )
    cached = _cache.get(key)
    if cached is not None:
        return cached

    # Expensive query
    rows = _run_real_query(filters, sort)
    _cache.set(key, rows)
    return rows


def invalidate():
    _cache.invalidate()


def stats():
    return _cache.stats()
```

## Patrón con persistencia a disco

Para datos que valen la pena sobrevivir reinicios (p.ej. resultados de queries sobre datos históricos inmutables):

```python
import pickle
import atexit
from pathlib import Path


_DISK_PATH = Path("cache/result_cache.pkl")


def load_from_disk() -> int:
    if not _DISK_PATH.exists():
        return 0
    try:
        with _DISK_PATH.open("rb") as f:
            data = pickle.load(f)
        with _cache._lock:
            _cache._data = OrderedDict(data)
        return len(data)
    except Exception:
        return 0


def dump_to_disk() -> None:
    _DISK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _cache._lock:
        data = dict(_cache._data)
    tmp = _DISK_PATH.with_suffix(".tmp")
    with tmp.open("wb") as f:
        pickle.dump(data, f)
    tmp.replace(_DISK_PATH)   # atomic on POSIX


# Register in create_app() (NOT in this module — only if not testing):
# if not _in_pytest():
#     load_from_disk()
#     atexit.register(dump_to_disk)
```

**Nota**: `atexit` **no siempre corre** en desktop (pywebview puede cerrar abruptamente). No asumas que el dump está siempre actualizado. Dump también en momentos específicos (tras un cambio grande, por ejemplo).

## Invariantes críticos

### 1 — Cada discriminador de tenancy va en la clave

Si tu app tiene **cualquier** concepto de "esto es de este user/producto/organización", **debe** formar parte de la clave de cache.

**Mal**:

```python
key = (filters, sort)
```

**Bien**:

```python
key = (user_id, tenant_id, filters, sort)
```

Si no lo haces, el cache **cross-contamina** resultados entre tenants. Es un bug de datos corruptos, no de rendimiento.

### 2 — Dos filtros distintos que "coinciden" por casualidad no deben colisionar

Si tu query hace resolución en dos pasos (`filters → keys → dataset`), **cada paso** necesita su propia clave, y la clave del segundo debe incluir un hash del primero — aunque los outputs intermedios coincidan.

Ejemplo real de Conter Stats:

```python
# WRONG — two filter sets that resolve to the same keys collide
page_cache_key = (view, sorted(keys), columns)

# RIGHT — include a hash of the original filter spec
page_cache_key = (view, sorted(keys), columns, filters_hash)
```

### 3 — Invalidar en mutaciones

Cualquier endpoint que escribe (`POST/PUT/PATCH/DELETE`) que afecta datos cacheados debe invalidar:

```python
@app.post("/api/workspaces")
def create_workspace():
    workspace_service.create(...)
    chart_agg_cache.invalidate()  # charts may have been affected
    return jsonify({"ok": True})
```

Mejor sobre-invalidar que dejar datos stale.

### 4 — No cachear datos mutables sin TTL

Si los datos cambian (registros live), cachea con TTL:

```python
entry = {"value": rows, "expires_at": time.time() + 60}
```

Si son inmutables (históricos antiguos, reportes congelados), no necesitan TTL.

## Admin UI

Añade endpoints para ver stats e invalidar manualmente. Útil cuando sospechas corrupción de cache:

```python
@admin_bp.get("/api/admin/cache/stats")
def cache_stats():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403
    from app.services import result_cache, other_cache
    return jsonify({
        "result_cache": result_cache.stats(),
        "other_cache":  other_cache.stats(),
    })


@admin_bp.post("/api/admin/cache/clear-ram")
def clear_ram():
    if not session.get("is_admin"):
        return jsonify({"error": "Admin only"}), 403
    from app.services import result_cache, other_cache
    result_cache.invalidate()
    other_cache.invalidate()
    return jsonify({"ok": True})
```

## Pitfalls comunes

- ❌ **Cachear resultados con listas grandes de floats**: pickle funciona pero puede ser lento de serializar. Considera MessagePack si el dump es demasiado costoso.
- ❌ **Usar `@functools.lru_cache` en funciones de servicio**: no es thread-safe en todos los casos, y no te da invalidación global selectiva. Prefiere el patrón LRU custom.
- ❌ **Asumir que `atexit` siempre corre**: en crashes y en desktop pywebview cerrado abruptamente, no siempre. Dump defensivo.
- ❌ **Crecer el cache sin bound**: el `maxsize` debe ser finito. Un cache de MB sin bound crece a GB en días.
- ❌ **Claves no-determinísticas**: `dict` no ordenado como parte de la clave produce hits aleatorios. Normaliza siempre a `tuple(sorted(...))`.

## Cuándo NO usar este patrón

- **Multi-proceso distribuido** (balanceador delante de N instancias Flask): las caches no se comparten. Usa Redis.
- **Datos altamente volátiles** (cambian cada pocos segundos): TTL < query time → cache inútil.
- **Contenido confidencial cross-tenant**: si el riesgo de colisión de claves es inaceptable incluso con un bug, considera per-user caches separados o no cachear.
