# 04 · PyInstaller spec

Un solo `my_app.spec` produce `.app` (macOS) y `.exe` (Windows) del mismo código.

## `my_app.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path.cwd()

a = Analysis(
    ['run.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'app' / 'templates'), 'app/templates'),
        (str(ROOT / 'app' / 'static'),    'app/static'),
        (str(ROOT / 'certs'),             'certs'),           # if you ship SSL
        (str(ROOT / 'app' / 'translations'), 'app/translations'),  # if i18n
    ],
    hiddenimports=[
        'app',
        'app.routes', 'app.routes.main', 'app.routes.api',
        'app.routes.admin', 'app.routes.auth',
        'app.services',
        'app.services.settings_service',
        'app.services.auth_service',
        # Add dynamically-imported services here as the project grows
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

ICON = str(ROOT / 'app' / 'static' / 'img' / 'icon.png')

if sys.platform == 'darwin':
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name='MyApp',
        console=False,
        upx=True,
        icon=ICON,
    )
    coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='MyApp')
    app = BUNDLE(
        coll,
        name='MyApp.app',
        bundle_identifier='com.example.myapp',
        icon=ICON,
        info_plist={'NSHighResolutionCapable': True},
    )
else:
    # Windows / Linux: single-file executable
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='MyApp',
        console=False,
        upx=True,
        icon=ICON,
    )
```

## Adaptaciones

- **Nombre del proyecto** — reemplaza `MyApp` en todo el spec.
- **`bundle_identifier`** — único por app en macOS. Convención: reverse-DNS (`com.yourorg.myapp`).
- **`datas`** — añade cualquier directorio que tu app lea en runtime: templates, static, certs, translations, seeds, configs. **No** añadas el código Python — eso se compila automáticamente.
- **`hiddenimports`** — si PyInstaller no detecta un import (vía `importlib`, `__import__`, string dinámico), listalo aquí. Regla: cuando el bundle arranca y lanza `ModuleNotFoundError`, añades el módulo aquí.

## Construir

```bash
pip install -e ".[build]"
pyinstaller my_app.spec
```

Output:

```
dist/
├── MyApp.app/                # macOS
│   └── Contents/{Info.plist, MacOS/MyApp, Resources/}
└── MyApp.exe                 # Windows
```

## Paths en runtime

El bundle lee archivos de `sys._MEIPASS` en tiempo de ejecución, pero los persistentes (SQLite, cache) viven en el home del user. Pattern:

```python
def _get_resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relative)


def _get_user_data_path(filename: str) -> str:
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = os.path.join(os.environ["APPDATA"], "My App")
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support/My App")
        else:
            base = os.path.expanduser("~/.my-app")
        os.makedirs(base, exist_ok=True)
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, filename)
```

- **Recursos bundleados** (templates, certs, traducciones) → `_get_resource_path()`.
- **Datos del user** (settings.db, cache/) → `_get_user_data_path()`.

Mezclar los dos es un bug común: si escribes `settings.db` en `sys._MEIPASS`, el siguiente arranque lo pierde (el bundle se re-extrae).

## Opciones clave

| Opción | Por qué |
|---|---|
| `console=False` | No abrir terminal al arrancar la app. En dev, `True` temporal es útil para ver stdout. |
| `upx=True` | Comprime binarios ~30%. Puede disparar antivirus falsos positivos en Windows — alternativa: `upx=False`. |
| `exclude_binaries=True` (macOS) | Requerido para que COLLECT + BUNDLE produzca un `.app` estructurado (no un single-file). |
| `exclude_binaries=False` (Windows) | Produce `.exe` single-file. Más cómodo de distribuir; si rompe, cambia a directorio-mode igual que macOS. |

## Troubleshooting rápido

| Síntoma | Fix |
|---|---|
| `ModuleNotFoundError` al abrir bundle | Añadir a `hiddenimports` |
| `TemplateNotFound` | Revisar `datas` + que `os.chdir(sys._MEIPASS)` corra |
| `.app` abre blanco | Ejecuta desde terminal (`./dist/MyApp.app/Contents/MacOS/MyApp`) para ver stdout |
| Gatekeeper lo rechaza | Unsigned — "System Settings → Privacy → Open Anyway" la primera vez |
| SmartScreen warning en Windows | Unsigned — "More info → Run anyway" |
| Binario >200MB | UPX off / deps pesadas. Revisar `excludes=[...]` para quitar módulos innecesarios |

## Code signing

Opcional y caro:

- **macOS**: Apple Developer Program ($99/año) + `codesign` + notarización.
- **Windows**: EV/OV certificate (~$200-500/año).

Para apps internas, usualmente se salta — el usuario acepta una vez el warning y ya.
