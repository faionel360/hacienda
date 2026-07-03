# Publicar la PWA en GitHub Pages — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar la app de códigos de Costa Rica en una URL pública de GitHub
Pages para que se pueda instalar como ícono en el iPhone (y compartir el link
con cualquiera).

**Architecture:** Renombrar la carpeta `web/` a `docs/` (convención que GitHub
Pages sirve sin configuración extra), inicializar git, subir el proyecto a un
repositorio público nuevo con `gh` (GitHub CLI), y activar GitHub Pages
apuntando a `main` / `/docs`.

**Tech Stack:** git, GitHub CLI (`gh`), GitHub Pages. Sin frameworks, sin CI.

## Global Constraints

- El repositorio debe ser público (requisito de GitHub Pages gratis en cuentas personales).
- No se debe subir `.venv/` ni `__pycache__/` al repositorio.
- Todo texto de commits y verificación en español, consistente con el resto del proyecto.
- No usar `--force` en ningún comando de git.

---

### Task 1: Renombrar `web/` a `docs/` y actualizar las referencias

**Files:**
- Rename: `web/` → `docs/` (con todo su contenido: `index.html`, `style.css`, `app.js`, `data.js`, `manifest.json`, `sw.js`, `icons/`)
- Modify: `.claude/launch.json` (el argumento `--directory web` pasa a `--directory docs`)
- Modify: `scripts/extraer_datos.py` (la línea que arma `OUT_JS` apunta a `web` y debe apuntar a `docs`)

**Interfaces:**
- Consumes: nada de tareas anteriores (es la primera tarea).
- Produces: la carpeta `docs/` con el mismo contenido que tenía `web/`, que las tareas 4 y 5 publicarán tal cual.

- [ ] **Step 1: Renombrar la carpeta**

```bash
git -C /home/allan/hacienda mv web docs 2>/dev/null || mv /home/allan/hacienda/web /home/allan/hacienda/docs
```

(usa `mv` normal porque git todavía no está inicializado en este proyecto; el
`git mv` es solo un intento por si ya existiera)

- [ ] **Step 2: Verificar que la carpeta se movió completa**

Run: `ls /home/allan/hacienda/docs`
Expected: `app.js  data.js  icons  index.html  manifest.json  style.css  sw.js`

Run: `ls /home/allan/hacienda/web 2>&1`
Expected: `No such file or directory` (la carpeta vieja ya no existe)

- [ ] **Step 3: Actualizar `.claude/launch.json`**

Contenido nuevo completo del archivo:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "web-local",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["-m", "http.server", "8123", "--directory", "docs"],
      "port": 8123
    }
  ]
}
```

- [ ] **Step 4: Actualizar la ruta de salida en `scripts/extraer_datos.py`**

Buscar la línea:
```python
OUT_JS = Path(__file__).resolve().parent.parent / "web" / "data.js"
```
Reemplazar por:
```python
OUT_JS = Path(__file__).resolve().parent.parent / "docs" / "data.js"
```

- [ ] **Step 5: Verificar que no queda ninguna referencia a la carpeta vieja**

Run: `grep -rn '"web"' /home/allan/hacienda/.claude /home/allan/hacienda/scripts`
Expected: sin resultados (ningún archivo debe mencionar la carpeta `web` como ruta)

---

### Task 2: Preparar el repositorio git local

**Files:**
- Create: `.gitignore`
- Create (implícito): repositorio git en `/home/allan/hacienda`

**Interfaces:**
- Consumes: el estado de archivos producido por la Task 1 (carpeta `docs/` ya renombrada).
- Produces: un repositorio git local con un primer commit, listo para conectarse a GitHub en la Task 4.

- [ ] **Step 1: Crear `.gitignore`**

```
.venv/
__pycache__/
*.pyc
```

- [ ] **Step 2: Inicializar git y hacer el primer commit**

```bash
cd /home/allan/hacienda
git init
git add scripts data docs especificaciones .claude .gitignore
git commit -m "Primera versión: buscador de códigos de Costa Rica (provincia, cantón, distrito, barrio)"
```

- [ ] **Step 3: Verificar el commit**

Run: `git -C /home/allan/hacienda log --oneline`
Expected: una línea con el mensaje del commit anterior.

Run: `git -C /home/allan/hacienda status`
Expected: `nothing to commit, working tree clean`

---

### Task 3: Conectar `gh` con la cuenta de GitHub (paso manual de Allan)

**Files:** ninguno.

**Interfaces:**
- Consumes: nada.
- Produces: una sesión autenticada de `gh` que la Task 4 necesita para crear el repositorio.

- [ ] **Step 1: Allan corre el login de forma interactiva**

Run (Allan lo ejecuta él mismo en su terminal, requiere abrir el navegador y confirmar un código):
```bash
gh auth login
```
Opciones a elegir cuando pregunte: `GitHub.com` → `HTTPS` → `Login with a web browser`.

- [ ] **Step 2: Verificar que quedó conectado**

Run: `gh auth status`
Expected: algo como `Logged in to github.com account <usuario> (...)`

---

### Task 4: Crear el repositorio en GitHub y subir el código

**Files:** ninguno (solo comandos de git/gh).

**Interfaces:**
- Consumes: repositorio git local de la Task 2, sesión autenticada de la Task 3.
- Produces: repositorio remoto público en GitHub con el código subido a `main`. Su nombre (`hacienda` por defecto) y el usuario resultante (`gh api user -q .login`) los usa la Task 5 para armar la URL de Pages.

- [ ] **Step 1: Crear el repo y subir el código**

```bash
cd /home/allan/hacienda
gh repo create hacienda --public --source=. --remote=origin --push
```

- [ ] **Step 2: Verificar que quedó público y con el código subido**

Run: `gh repo view --json name,visibility,url`
Expected: JSON con `"visibility":"PUBLIC"` y una `url` de github.com

Run: `git -C /home/allan/hacienda log origin/main --oneline`
Expected: la misma línea de commit que en la Task 2.

---

### Task 5: Activar GitHub Pages apuntando a `main` / `/docs`

**Files:** ninguno (configuración vía API de GitHub).

**Interfaces:**
- Consumes: repositorio remoto de la Task 4.
- Produces: la URL pública `https://<usuario>.github.io/hacienda/`, verificada en la Task 6.

- [ ] **Step 1: Activar Pages**

```bash
cd /home/allan/hacienda
gh api repos/{owner}/{repo}/pages -X POST --input - <<'EOF'
{
  "source": {
    "branch": "main",
    "path": "/docs"
  }
}
EOF
```

(`{owner}/{repo}` los resuelve `gh` automáticamente contra el repo actual;
`--input -` manda el JSON completo por entrada estándar, la forma más segura
de enviar campos anidados como `source.branch`/`source.path`)

- [ ] **Step 2: Confirmar que quedó configurado**

Run: `gh api repos/{owner}/{repo}/pages`
Expected: JSON con `"status"` que pasa de `"building"` a `"built"` en uno o dos
minutos, y un campo `"html_url"` con la URL pública.

---

### Task 6: Verificar que la app publicada funciona igual que la local

**Files:** ninguno.

**Interfaces:**
- Consumes: URL pública de la Task 5.
- Produces: confirmación final de que el proyecto quedó publicado correctamente.

- [ ] **Step 1: Esperar a que el sitio esté disponible y comprobar el HTML**

Run (reintentar cada 15-20s hasta 2 minutos si da 404, GitHub Pages tarda en desplegar):
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<usuario>.github.io/hacienda/
```
Expected: `200`

- [ ] **Step 2: Confirmar que trae el contenido esperado**

Run:
```bash
curl -s https://<usuario>.github.io/hacienda/ | grep -o "Códigos de Costa Rica"
```
Expected: `Códigos de Costa Rica`

- [ ] **Step 3: Confirmar que `data.js` (los datos) carga bien**

Run:
```bash
curl -s -o /dev/null -w "%{http_code} %{size_download}\n" https://<usuario>.github.io/hacienda/data.js
```
Expected: código `200` y un tamaño mayor a 200000 (bytes) — confirma que se
subieron los ~6600 barrios completos, no un archivo vacío o truncado.

---

## Después del plan (no es una tarea de código)

Una vez la Task 6 confirme que todo carga bien, el siguiente paso es que Allan,
desde su iPhone, abra esa URL en Safari y use "Compartir" → "Agregar a Inicio".
Esto no requiere ningún comando ni cambio de código — es una instrucción para
comunicarle directamente al terminar el plan.
