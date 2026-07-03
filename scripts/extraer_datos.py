"""
Extrae la tabla de Provincia/Cantón/Distrito/Barrio del PDF oficial y genera:
  - data/costa-rica.json  (estructura jerárquica, para revisar/editar a mano)
  - docs/data.js          (los mismos datos como `const DATA_CR = {...}`,
                            para que la página web los cargue sin servidor)

El PDF es un export de Excel: cada página dibuja el mismo grid de columnas en
las mismas posiciones (verificado en varias páginas), pero las dos últimas
columnas (Barrio, Nombre Barrio) no tienen una línea vertical que las separe,
así que pdfplumber no las detecta como tabla con su modo automático. Por eso
acá se arma la tabla a mano: se usan las líneas horizontales delgadas (rects)
para saber dónde empieza y termina cada fila, y las posiciones X conocidas de
columna para decidir a qué columna pertenece cada palabra.

Requiere: pdfplumber (pip install --user pdfplumber)
"""

import json
import re
from pathlib import Path

import pdfplumber

PDF_PATH = Path("/home/allan/Descargas/Codificacion,canton,provincia,distritoybarrio.pdf")
OUT_JSON = Path(__file__).resolve().parent.parent / "data" / "costa-rica.json"
OUT_JS = Path(__file__).resolve().parent.parent / "docs" / "data.js"

# Borde izquierdo (x0) de cada una de las 7 columnas detectables por línea.
# La 7ª columna incluye Barrio + Nombre Barrio juntos (no hay línea entre
# ellas); se separan después con una expresión regular.
COL_BOUNDS = [49.9, 95.0, 175.6, 212.7, 305.3, 342.4, 498.8]

BARRIO_RE = re.compile(r"^(\d+)\s*(.*)$")


def columna_de(x0: float) -> int:
    idx = 0
    for i, borde in enumerate(COL_BOUNDS):
        if x0 >= borde:
            idx = i
        else:
            break
    return idx


def filas_de_pagina(page) -> list[list[str]]:
    """Reconstruye las filas de la tabla de una página como listas de 7 textos."""
    bordes_fila = sorted({round(r["top"], 1) for r in page.rects if r["height"] < 3})
    if len(bordes_fila) < 2:
        return []

    palabras = page.extract_words(use_text_flow=False, keep_blank_chars=False)

    # Cuando un grupo de barrios sigue en la página siguiente, la primera fila
    # de la nueva página no tiene línea de borde superior propia (esa línea
    # quedó dibujada en la página anterior). Si hay texto por encima del primer
    # borde detectado, se agrega un borde sintético para no perder esa fila.
    altura_fila = bordes_fila[1] - bordes_fila[0]
    primer_texto = min((w["top"] for w in palabras), default=bordes_fila[0])
    if primer_texto < bordes_fila[0] - 0.5:
        bordes_fila = [bordes_fila[0] - altura_fila] + bordes_fila

    filas = []
    for y0, y1 in zip(bordes_fila[:-1], bordes_fila[1:]):
        palabras_fila = [w for w in palabras if y0 - 0.5 <= w["top"] < y1 - 0.5]
        if not palabras_fila:
            continue
        columnas = ["" for _ in range(7)]
        for w in sorted(palabras_fila, key=lambda w: w["x0"]):
            i = columna_de(w["x0"])
            columnas[i] = f"{columnas[i]} {w['text']}".strip()
        filas.append(columnas)
    return filas


def limpiar_nombre(nombre: str) -> str:
    nombre = nombre.strip()
    if nombre.endswith("."):
        nombre = nombre[:-1].strip()
    return nombre


def procesar_pdf() -> dict:
    provincias: dict[int, dict] = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        for num_pagina, page in enumerate(pdf.pages, start=1):
            for fila in filas_de_pagina(page):
                prov_num, prov_nombre, canton_num, canton_nombre, dist_num, dist_nombre, barrio_col = fila

                if not prov_num.isdigit():
                    # Fila de encabezado repetida en cada página.
                    continue

                m = BARRIO_RE.match(barrio_col)
                if not m:
                    raise ValueError(
                        f"Página {num_pagina}: no pude separar número/nombre de barrio "
                        f"en {barrio_col!r} (fila: {fila})"
                    )
                barrio_num, barrio_nombre = m.group(1), m.group(2)

                prov_num = int(prov_num)
                canton_num = int(canton_num)
                dist_num = int(dist_num)
                barrio_num = int(barrio_num)

                provincia = provincias.setdefault(
                    prov_num, {"numero": prov_num, "nombre": limpiar_nombre(prov_nombre), "cantones": {}}
                )
                canton = provincia["cantones"].setdefault(
                    canton_num, {"numero": canton_num, "nombre": limpiar_nombre(canton_nombre), "distritos": {}}
                )
                distrito = canton["distritos"].setdefault(
                    dist_num, {"numero": dist_num, "nombre": limpiar_nombre(dist_nombre), "barrios": []}
                )
                distrito["barrios"].append({"numero": barrio_num, "nombre": limpiar_nombre(barrio_nombre)})

    return provincias


def a_listas_ordenadas(provincias: dict) -> dict:
    """Convierte los dict intermedios (indexados por número) en listas ordenadas."""
    resultado = []
    for prov in sorted(provincias.values(), key=lambda p: p["numero"]):
        cantones = []
        for canton in sorted(prov["cantones"].values(), key=lambda c: c["numero"]):
            distritos = []
            for distrito in sorted(canton["distritos"].values(), key=lambda d: d["numero"]):
                barrios = sorted(distrito["barrios"], key=lambda b: b["numero"])
                distritos.append({"numero": distrito["numero"], "nombre": distrito["nombre"], "barrios": barrios})
            cantones.append({"numero": canton["numero"], "nombre": canton["nombre"], "distritos": distritos})
        resultado.append({"numero": prov["numero"], "nombre": prov["nombre"], "cantones": cantones})
    return {"provincias": resultado}


def validar(data: dict) -> list[str]:
    """Revisa huecos en la numeración y nombres vacíos. Devuelve una lista de avisos."""
    avisos = []
    provincias = data["provincias"]

    numeros_prov = [p["numero"] for p in provincias]
    if numeros_prov != list(range(1, len(numeros_prov) + 1)):
        avisos.append(f"Números de provincia con huecos o desordenados: {numeros_prov}")

    total_cantones = total_distritos = total_barrios = 0
    for prov in provincias:
        if not prov["nombre"]:
            avisos.append(f"Provincia {prov['numero']} sin nombre")
        numeros_canton = [c["numero"] for c in prov["cantones"]]
        if numeros_canton != list(range(1, len(numeros_canton) + 1)):
            avisos.append(f"Provincia {prov['numero']} ({prov['nombre']}): cantones con huecos: {numeros_canton}")
        for canton in prov["cantones"]:
            total_cantones += 1
            if not canton["nombre"]:
                avisos.append(f"Cantón {prov['numero']}-{canton['numero']} sin nombre")
            numeros_dist = [d["numero"] for d in canton["distritos"]]
            if numeros_dist != list(range(1, len(numeros_dist) + 1)):
                avisos.append(
                    f"Cantón {prov['numero']}-{canton['numero']} ({canton['nombre']}): "
                    f"distritos con huecos: {numeros_dist}"
                )
            for distrito in canton["distritos"]:
                total_distritos += 1
                if not distrito["nombre"]:
                    avisos.append(f"Distrito {prov['numero']}-{canton['numero']}-{distrito['numero']} sin nombre")
                numeros_barrio = [b["numero"] for b in distrito["barrios"]]
                if numeros_barrio != list(range(1, len(numeros_barrio) + 1)):
                    avisos.append(
                        f"Distrito {prov['numero']}-{canton['numero']}-{distrito['numero']} "
                        f"({distrito['nombre']}): barrios con huecos: {numeros_barrio}"
                    )
                for barrio in distrito["barrios"]:
                    total_barrios += 1
                    if not barrio["nombre"]:
                        avisos.append(
                            f"Barrio {prov['numero']}-{canton['numero']}-{distrito['numero']}-"
                            f"{barrio['numero']} sin nombre"
                        )

    print(
        f"Resumen: {len(provincias)} provincias, {total_cantones} cantones, "
        f"{total_distritos} distritos, {total_barrios} barrios."
    )
    return avisos


def main():
    provincias = procesar_pdf()
    data = a_listas_ordenadas(provincias)

    avisos = validar(data)
    if avisos:
        print(f"\n{len(avisos)} avisos de validación:")
        for a in avisos:
            print(" -", a)
    else:
        print("Sin avisos de validación: numeración consecutiva y sin nombres vacíos.")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado {OUT_JSON}")

    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    js_contenido = "// Generado automáticamente por scripts/extraer_datos.py — no editar a mano.\n"
    js_contenido += "const DATA_CR = " + json.dumps(data, ensure_ascii=False) + ";\n"
    OUT_JS.write_text(js_contenido, encoding="utf-8")
    print(f"Guardado {OUT_JS}")


if __name__ == "__main__":
    main()
