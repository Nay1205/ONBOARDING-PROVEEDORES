"""Prueba de extraccion de licencias de conducir (nombre, numero de
licencia, vigencia y CURP). Las licencias vienen de distintos estados y
cada uno tiene su propio diseno, asi que este script imprime una tabla
comparativa para revisar la calidad antes de escribirlo en el Excel.

Uso:
    .venv\\Scripts\\python.exe extraer_licencias.py "LICENCIAS-....zip"
"""
import argparse
import csv
import sys
import tempfile
import zipfile
from pathlib import Path

from extractor import ocr, parsers

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".pdf"}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_o_carpeta", help="Ruta al .zip de licencias, o a una carpeta ya descomprimida")
    parser.add_argument("--csv", default="reporte_licencias.csv", help="Donde guardar el reporte en CSV")
    return parser.parse_args()


def obtener_carpeta(ruta: Path, carpeta_temporal: Path) -> Path:
    if ruta.is_dir():
        return ruta
    with zipfile.ZipFile(ruta) as zf:
        zf.extractall(carpeta_temporal)
    return carpeta_temporal


def procesar_licencia(path: Path) -> dict:
    texto = ocr.extract_text(path)
    nombre_ocr = parsers.find_nombre_licencia(texto)
    nombre_archivo = parsers.derive_nombre_desde_archivo(path.name)
    curp, curp_validado = parsers.find_curp_candidato(texto)
    return {
        "archivo": path.name,
        "nombre_ocr": nombre_ocr or "",
        "nombre_archivo": nombre_archivo,
        "coincide_nombre": _nombres_parecidos(nombre_ocr, nombre_archivo),
        "num_licencia": parsers.find_numero_licencia(texto) or "",
        "vigencia": parsers.find_vigencia_licencia(texto) or "",
        "curp": curp or "",
        "curp_validado": "si" if curp_validado else ("no" if curp else ""),
    }


def _nombres_parecidos(nombre_ocr: str | None, nombre_archivo: str) -> str:
    if not nombre_ocr:
        return "(sin ocr)"
    palabras_ocr = set(nombre_ocr.split())
    palabras_archivo = set(nombre_archivo.split())
    comunes = palabras_ocr & palabras_archivo
    if len(comunes) >= min(2, len(palabras_archivo)):
        return "si"
    return "REVISAR"


def main():
    args = parse_args()
    ocr.configure_tesseract()
    entrada = Path(args.zip_o_carpeta)
    if not entrada.exists():
        sys.exit(f"No existe: {entrada}")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = obtener_carpeta(entrada, Path(tmp))
        archivos = sorted(
            p for p in carpeta.rglob("*")
            if p.is_file() and p.suffix.lower() in EXTENSIONES_VALIDAS
        )
        filas = [procesar_licencia(p) for p in archivos]

    columnas = [
        "archivo", "nombre_ocr", "nombre_archivo", "coincide_nombre",
        "num_licencia", "vigencia", "curp", "curp_validado",
    ]
    with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    for fila in filas:
        print("=====", fila["archivo"], "=====")
        print(f"  Nombre (OCR):     {fila['nombre_ocr'] or '(no encontrado)'}")
        print(f"  Nombre (archivo): {fila['nombre_archivo']}")
        if fila["coincide_nombre"] == "REVISAR":
            print("  >> el nombre del archivo y el de la foto no coinciden, revisar")
        print(f"  Número de licencia: {fila['num_licencia'] or '(no encontrado)'}")
        print(f"  Vigencia:            {fila['vigencia'] or '(no encontrado)'}")
        etiqueta_curp = "" if not fila["curp"] else (
            " (sin validar, revisar)" if fila["curp_validado"] == "no" else ""
        )
        print(f"  CURP: {fila['curp'] or '(no encontrado)'}{etiqueta_curp}")
        print()

    print(f"Reporte completo guardado en: {args.csv}")


if __name__ == "__main__":
    main()
