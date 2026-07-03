# Publicar la app como PWA en GitHub Pages (para iPhone y para compartir)

## Contexto

Allan ya tiene una app web local funcionando (buscador de códigos de
Provincia/Cantón/Distrito/Barrio de Costa Rica) con soporte de PWA (manifest.json
+ service worker), pero solo existe como archivos en su computadora Linux. Quiere
poder abrirla como un ícono en su propio iPhone y, más adelante, poder compartir
el enlace con otras personas.

Evaluamos llevarla a una app nativa de iOS (con Capacitor + Xcode), pero eso exige
una Mac (no disponible) y una cuenta de Apple Developer Program (99 USD/año) incluso
solo para instalarla en su propio teléfono — no hay forma gratuita de evitarlo.
Allan decidió quedarse con la ruta PWA (gratis, sin Apple de por medio), que ya
cumple el objetivo real: un ícono que abre la app y funciona sin internet.

Para que Safari pueda instalarla como PWA, la app necesita servirse desde una
dirección `https://`, no desde un archivo local — de ahí la necesidad de
publicarla en algún lugar. Elegimos GitHub Pages (gratis, ya usa GitHub, no
depende de que su computadora esté encendida) sobre exponerla solo en su WiFi
de casa. Como beneficio directo, una URL pública también resuelve el pedido de
"compartirlo": cualquiera puede abrir el mismo link y agregarlo a su propia
pantalla de inicio.

## Diseño

**Reestructuración de carpetas**: renombrar `web/` a `docs/`. Es la convención
que reconoce GitHub Pages para servir contenido directamente desde una carpeta
del repositorio sin configurar nada adicional (sin flujos de GitHub Actions).
El resto del proyecto (`scripts/`, `data/`, `especificaciones/`) no se sirve al
público — GitHub Pages solo publica lo que hay dentro de `docs/`.

**Repositorio**: se crea un repo nuevo en GitHub llamado `hacienda` (ajustable
si Allan prefiere otro nombre), público (requisito de GitHub Pages gratis en
cuentas personales). Se sube todo el proyecto: script de extracción, datos y la
app. Los datos son códigos geográficos oficiales de Costa Rica, nada sensible.

**Exclusiones (.gitignore)**: se excluye `.venv/` (entorno virtual de Python
usado solo para correr el script de extracción, no debe subirse a git) y
`__pycache__/`.

**Paso manual de Allan**: `gh` (la herramienta de línea de comandos de GitHub)
está instalada pero no conectada a su cuenta. Allan debe correr
`gh auth login` y completar el flujo en pantalla (abre navegador, confirma
código) — es un paso que requiere su interacción directa y no se puede
automatizar por él.

**Activar GitHub Pages**: una vez el repo existe en GitHub, se activa Pages
apuntando a la rama `main`, carpeta `/docs`, usando `gh api` o la configuración
del repositorio. Resultado: una URL pública tipo
`https://<usuario-de-github>.github.io/hacienda/`.

**Verificación**: abrir esa URL en un navegador para confirmar que carga igual
que la versión local (mismo comportamiento, mismos datos). Luego instrucciones
para Allan: en el iPhone, abrir la URL en Safari → botón compartir → "Agregar a
Inicio", y confirmar que el ícono abre la app y funciona incluso en modo avión
(gracias al service worker que cachea los archivos).

## Fuera de alcance

- Publicar en la App Store de Apple (requiere Mac + cuenta paga, descartado por Allan).
- Dominio propio o hosting de pago — GitHub Pages es suficiente por ahora.
- Actualizaciones automáticas de datos: si el PDF oficial cambia en el futuro,
  hay que volver a correr `scripts/extraer_datos.py` a mano y subir los cambios.
