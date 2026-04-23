# 03 · Dual runtime (web + desktop)

Un solo `run.py` que sirve la app en navegador o en ventana nativa pywebview.

## `run.py`

```python
"""
Entry point for both web (browser) and desktop (pywebview window) runtimes.

Usage:
    python run.py                         # Web, port 5000
    python run.py --port 8080             # Web, custom port
    python run.py --desktop               # Desktop pywebview
    python run.py --desktop --port 8080
"""
import argparse
import os
import sys
import threading
from app import create_app


def _fix_frozen_cwd():
    """In a PyInstaller bundle, cwd is wherever the user ran it from;
    templates/static are relative to sys._MEIPASS. Force cwd so Flask finds them."""
    if getattr(sys, "frozen", False):
        os.chdir(sys._MEIPASS)


def run_web(host: str, port: int, ssl: tuple | None = None):
    app = create_app()
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        ssl_context=ssl,
        threaded=True,
    )


def run_desktop(port: int):
    """Flask on daemon thread + pywebview window. Window close kills the thread."""
    import webview

    app = create_app()

    def serve():
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
        )

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    # Give Flask a moment to bind the port
    import time
    for _ in range(20):
        time.sleep(0.1)

    webview.create_window(
        title="My App",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=800,
    )
    webview.start()


def main():
    _fix_frozen_cwd()

    parser = argparse.ArgumentParser()
    parser.add_argument("--desktop", action="store_true", help="Open in native window")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if args.desktop:
        run_desktop(args.port)
    else:
        run_web(args.host, args.port)


if __name__ == "__main__":
    main()
```

## Reglas críticas

### `use_reloader=False` siempre

Flask reloader hace `fork()` + `exec()` para respawnear al detectar cambios. En modo desktop, eso rompe pywebview (el hijo no hereda la webview del padre). En modo frozen, no tiene sentido (no hay `.py` que cambiar). Déjalo off en los dos modos.

### `threaded=True`

Sin esto, Flask procesa requests de uno en uno y el webview se congela si haces dos requests simultáneos (ej: filtro + carga de charts). `threaded=True` spawnea un thread por request — trivial para este volumen.

### Thread daemon para desktop

```python
t = threading.Thread(target=serve, daemon=True)
```

`daemon=True` → el thread muere con el proceso principal. Sin esto, cerrar la ventana pywebview dejaría Flask corriendo huérfano.

### `_fix_frozen_cwd()`

PyInstaller extrae templates/static a `sys._MEIPASS` al arrancar. Flask los busca relativos al **cwd**, no al módulo. Si el user ejecuta el binario desde el Finder/Explorer, el cwd puede ser cualquier cosa. `os.chdir(sys._MEIPASS)` fuerza el contexto correcto.

### Puerto por defecto 5000

Evita 8080 (común en otros servicios locales) y 80 (requires root). 5000 es Flask canonical. Scripts auxiliares (como un `screenshot.py`) suelen usar un puerto distinto (ej: 5111) para convivir con un dev server abierto.

## Variantes

### Con HTTPS self-signed

```python
def _ssl_context():
    cert = os.path.join(sys._MEIPASS if getattr(sys, "frozen", False) else ".", "certs/cert.pem")
    key  = os.path.join(sys._MEIPASS if getattr(sys, "frozen", False) else ".", "certs/key.pem")
    if os.path.exists(cert) and os.path.exists(key):
        return (cert, key)
    return None


run_web(host, port, ssl=_ssl_context())
```

Genera los certs una vez con `openssl req -x509 ...` y commitea en `certs/`. Nunca uses certs reales en bundles públicos.

### Sin pywebview (solo web)

Si no necesitas desktop, elimina `run_desktop()` y la dep `pywebview`. Mantén el resto del skeleton igual — `_fix_frozen_cwd()` sigue siendo útil si distribuyes `.exe`/`.app` aunque sea para servir web local.

### Server-only deploy (Docker)

El mismo `run.py` sirve como `CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "5000"]` en un Dockerfile. El `threaded=True` ya lo hace aceptable para tráfico bajo; para producción seria, gunicorn delante:

```
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

Nota que pasamos `app:create_app()` (la factory), no una instancia — gunicorn la llama.
