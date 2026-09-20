"""PMV (semana 3): lee la carpeta comprimida de un proveedor (fotos y PDFs),
extrae los datos con reglas programadas (sin IA) y los escribe como un
renglon nuevo en la hoja de calculo de proveedores.

Uso:
    .venv\\Scripts\\python.exe main.py "drive-download.zip" --cliente "MELI 2026"
"""
import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

from extractor.aggregate import procesar_carpeta_proveedor
from extractor.sheet_writer import escribir_registro, obtener_copia_de_prueba

CAMPOS_LEGIBLES = {
    "nombre_proveedor": "Nombre del proveedor",
    "rfc_proveedor": "RFC del proveedor",
    "nombre_driver": "Nombre del driver",
    "curp_driver": "CURP del driver",
    "rfc_driver": "RFC del driver",
    "num_licencia": "Número de licencia",
    "placas": "Placas",
    "anio": "Año",
    "marca": "Marca",
    "aseguradora": "Aseguradora",
    "numero_poliza": "Número de póliza",
    "exp_seguro": "Expiración del seguro",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_o_carpeta", help="Ruta al .zip descargado de Drive, o a una carpeta ya descomprimida")
    parser.add_argument("--cliente", required=True, help="Nombre exacto de la pestana del cliente, ej. 'MELI 2026'")
    parser.add_argument(
        "--excel",
        default="DATA OPERADORES EXTERNOS.xlsx",
        help="Excel original de proveedores (solo se lee, nunca se modifica)",
    )
    parser.add_argument(
        "--salida",
        default="DATA OPERADORES EXTERNOS (PRUEBA).xlsx",
        help="Copia de prueba donde se escriben los renglones nuevos",
    )
    return parser.parse_args()


def obtener_carpeta_proveedor(ruta: Path, carpeta_temporal: Path) -> Path:
    if ruta.is_dir():
        return ruta
    with zipfile.ZipFile(ruta) as zf:
        zf.extractall(carpeta_temporal)
    return carpeta_temporal


def main():
    args = parse_args()
    entrada = Path(args.zip_o_carpeta)
    if not entrada.exists():
        sys.exit(f"No existe: {entrada}")

    excel_original = Path(args.excel)
    if not excel_original.exists():
        sys.exit(f"No existe el Excel original: {excel_original}")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = obtener_carpeta_proveedor(entrada, Path(tmp))
        resultado = procesar_carpeta_proveedor(carpeta)

    print(f"\nArchivos procesados ({len(resultado.archivos_procesados)}):")
    for nombre in resultado.archivos_procesados:
        print(f"  - {nombre}")

    print("\nDatos extraidos:")
    for campo, etiqueta in CAMPOS_LEGIBLES.items():
        valor = resultado.valores.get(campo) or "(no encontrado)"
        print(f"  {etiqueta}: {valor}")

    if resultado.pendientes:
        print("\nPendientes de revisar a mano:")
        for pendiente in resultado.pendientes:
            print(f"  - {pendiente}")

    salida = obtener_copia_de_prueba(excel_original, Path(args.salida))
    try:
        fila = escribir_registro(salida, args.cliente, resultado.valores)
    except PermissionError:
        sys.exit(
            f"\nNo se pudo guardar: '{salida}' esta abierto en Excel. "
            "Cierralo e intenta de nuevo."
        )
    print(f"\nListo. Renglon escrito en fila {fila} de la pestana '{args.cliente}' en:\n  {salida}")


if __name__ == "__main__":
    main()
