# 05 · GitHub Actions — release + build con gate `/compile`

Dos workflows: `release.yml` (auto-versionado con `python-semantic-release`) y `build.yml` (PyInstaller en matrix macOS+Windows, condicional al `/compile`).

## `pyproject.toml` — sección semantic-release

```toml
[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "flask>=3.0",
    "pywebview>=5.0",
    # ...
]

[project.optional-dependencies]
build = ["pyinstaller>=6.0"]

[tool.semantic_release]
version_toml         = ["pyproject.toml:project.version"]
branch               = "master"
upload_to_vcs_release = true
commit_message       = "chore(release): {version}"

[tool.semantic_release.commit_parser_options]
allowed_tags = ["feat", "fix", "docs", "style", "refactor",
                "perf", "test", "chore", "ci", "build"]
minor_tags   = ["feat"]
patch_tags   = ["fix", "perf"]

[tool.semantic_release.changelog]

[tool.semantic_release.changelog.default_templates]
changelog_file = "CHANGELOG.md"

[tool.semantic_release.branches.master]
match = "(master|main)"
prerelease = false
```

## `.github/workflows/release.yml`

```yaml
name: Semantic Release

on:
  push:
    branches: [master, main]

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency: release
    permissions:
      id-token: write
      contents: write
    outputs:
      released: ${{ steps.semrel.outputs.released }}

    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0                      # semantic-release needs full history
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v6
        with:
          python-version: '3.11'

      - run: pip install python-semantic-release

      - name: Python Semantic Release
        id: semrel
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          semantic-release version
          semantic-release publish
          if git diff --name-only HEAD~1 HEAD | grep -q pyproject.toml; then
            echo "released=true" >> "$GITHUB_OUTPUT"
          fi

  build:
    needs: release
    if: needs.release.outputs.released == 'true' &&
        contains(github.event.head_commit.message, '/compile')
    uses: ./.github/workflows/build.yml
    permissions:
      contents: write
```

## `.github/workflows/build.yml`

```yaml
name: Build binaries

on:
  workflow_call:

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: macos-latest
            artifact: MyApp.app
            asset_name: MyApp-macOS.zip
          - os: windows-latest
            artifact: MyApp.exe
            asset_name: MyApp-Windows.zip
    runs-on: ${{ matrix.os }}
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v6
        with:
          python-version: '3.11'

      - run: pip install . pyinstaller pillow

      - run: pyinstaller my_app.spec

      - name: Package (macOS/Linux)
        if: matrix.os != 'windows-latest'
        run: |
          cd dist && zip -r ${{ matrix.asset_name }} ${{ matrix.artifact }}

      - name: Package (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          cd dist
          Compress-Archive -Path ${{ matrix.artifact }} -DestinationPath ${{ matrix.asset_name }}

      - uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.asset_name }}
          path: dist/${{ matrix.asset_name }}

      - name: Attach to release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          tag=$(git describe --tags --abbrev=0)
          gh release upload "$tag" "dist/${{ matrix.asset_name }}" --clobber
```

## Cómo funciona

### Commit → Release

Cada push a `master`/`main` dispara `release.yml`:

1. `semantic-release version` analiza los commits desde el último tag.
2. Según el tag del commit (`feat:`, `fix:`, etc.) decide bump.
3. Si hay bump: actualiza `pyproject.toml:version`, genera `CHANGELOG.md`, commit `chore(release): X.Y.Z`, tag `vX.Y.Z`, push.
4. `semantic-release publish` crea el GitHub Release con las notas.

### Release → Build (condicional)

El job `build` **solo** corre si:

- Hubo release (output `released == 'true'`), **y**
- El commit que disparó tiene `/compile` en el mensaje.

```
feat(charts): heatmap with annotations

/compile
```

→ Bumpea minor, compila macOS+Windows, sube `.zip` al Release.

```
fix(auth): typo in error
```

→ Bumpea patch, Release creado **sin binarios**. El user final no lo nota.

## Convenciones de commit

| Tag | Bump |
|---|---|
| `feat` | minor |
| `fix`, `perf` | patch |
| `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build` | none |
| `BREAKING CHANGE:` en body | major |

Formato:

```
<tag>(<scope>): <imperative message>

[optional body]

[optional BREAKING CHANGE: ...]
[optional /compile]
```

## Bootstrap en un repo nuevo

```bash
mkdir -p .github/workflows
# Copy release.yml and build.yml above
git add .github/workflows/
git add pyproject.toml
git commit -m "ci: set up semantic-release + build"
git push
```

Los primeros pushes no bumpearan (con tags `ci`, `chore`). Al primer `feat:` se crea `v0.1.0` (o el que toque según tu version inicial).

## Forzar un build sin feature

```bash
git commit --allow-empty -m "chore: trigger compile

/compile"
# Wait... chore doesn't bump, so build won't trigger (released=false)
```

Para forzar un compile, sube la versión con un `feat:` bogus o usa `--force`:

```bash
# Con commit real:
git commit -m "fix: recompile for distribution

/compile"
```

## Permisos necesarios

El workflow necesita:

- `contents: write` — para push de commits/tags.
- `id-token: write` — por si algún día usas trusted publishing.

El token por defecto (`secrets.GITHUB_TOKEN`) basta; no necesitas un PAT.

## Troubleshooting

| Síntoma | Fix |
|---|---|
| `semantic-release` no bumpea | Commit no usa tag válido; revisa `[tool.semantic_release.commit_parser_options]` |
| Release creado pero sin assets | Falta `/compile` en el commit |
| `build` falla en macOS: pillow | Añade `pip install pillow` — PyInstaller lo necesita para el icono |
| Dos releases simultáneos | `concurrency: release` lo previene; si pasa, cancela uno |
| `released=false` siempre | El check `git diff --name-only HEAD~1 HEAD` asume que el commit de release incluye `pyproject.toml`. Verifica que `version_toml` está configurado. |
