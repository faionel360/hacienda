# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

Buscador web de códigos oficiales de Costa Rica (Provincia → Cantón →
Distrito → Barrio, codificación de 2016). Es una PWA (Progressive Web App)
estática publicada en GitHub Pages: `https://<usuario>.github.io/hacienda/`.
Sin backend, sin build step, sin frameworks — HTML/CSS/JS planos servidos
directamente.

## Comandos

**Correr localmente:**
```bash
python3 -m http.server 8123 --directory docs
```
(También configurado en `.claude/launch.json` como la config `web-local`.)
Abrir `http://localhost:8123`.

**Regenerar los datos** (solo si cambia el PDF oficial de origen):
```bash
pip install --user pdfplumber
python3 scripts/extraer_datos.py
```
Requiere el PDF en `/home/allan/Descargas/Codificacion,canton,provincia,distritoybarrio.pdf`
(ruta hardcodeada en el script). Regenera `data/costa-rica.json` y `docs/data.js`.

No hay tests, linter, ni proceso de build — es JS/HTML/CSS servido tal cual.

## Arquitectura

**`docs/`** es la carpeta que GitHub Pages sirve públicamente (convención de
Pages: rama `main`, carpeta `/docs`, sin GitHub Actions). Todo lo demás en el
repo (`scripts/`, `data/`, `especificaciones/`) es soporte interno, no se
publica.

**Flujo de datos** (unidireccional, un solo sentido):
`scripts/extraer_datos.py` parsea el PDF oficial → genera dos salidas
equivalentes: `data/costa-rica.json` (para revisar/editar a mano) y
`docs/data.js` (los mismos datos como `const DATA_CR = {...}`, cargado por
la página vía `<script>` porque no hay servidor que sirva JSON dinámicamente).
`docs/data.js` está marcado como generado automáticamente — no editarlo a
mano, correr el script de nuevo.

**Extracción del PDF** (`scripts/extraer_datos.py`): el PDF es un export de
Excel con la misma grilla de columnas en cada página. `pdfplumber` no detecta
la tabla automáticamente porque faltan líneas verticales entre las columnas
de Barrio y Nombre Barrio, así que el script arma las filas a mano usando las
líneas horizontales (`rects`) para los límites de fila y posiciones X fijas
(`COL_BOUNDS`) para asignar cada palabra a su columna. Incluye una función
`validar()` que revisa huecos en la numeración y nombres vacíos antes de
guardar.

**Frontend** (`docs/app.js`): buscador encadenado de 4 niveles (provincia →
cantón → distrito → barrio) implementado con una clase `Nivel` reutilizada
por cada campo. Cada nivel se habilita solo cuando el nivel anterior tiene
selección; los datos de cada nivel salen del nivel padre seleccionado
(`nivelCanton` lee `nivelProvincia.seleccion.cantones`, etc.). Todo en un
único IIFE, sin módulos ni build — `data.js` se carga antes que `app.js` en
`index.html` para que `DATA_CR` ya exista como global.

**PWA** (`docs/manifest.json` + `docs/sw.js`): service worker con estrategia
cache-first simple, cachea todos los archivos estáticos en el install para
que la app funcione sin conexión tras la primera visita o tras "Agregar a
inicio" en el celular. Al editar cualquier archivo cacheado (`app.js`,
`style.css`, `index.html`, `data.js`), hay que subir el número de versión en
`CACHE` (`docs/sw.js`) — si no, los usuarios que ya instalaron la PWA
seguirán viendo la versión vieja porque el service worker no vuelve a
descargar archivos con el mismo nombre de caché.

## Notas de estilo del proyecto

- Todo el código (comentarios, mensajes, UI) está en **español**.
- Sin dependencias de frontend — no introducir frameworks ni bundlers sin
  discutirlo primero con Allan.
