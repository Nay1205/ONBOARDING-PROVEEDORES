"""Escribe un registro extraido como renglon nuevo en la pestana del
cliente correspondiente, dentro del archivo de Excel de proveedores.
"""
import re
import shutil
import unicodedata
from pathlib import Path

import openpyxl


def _normalizar(texto: str) -> str:
    texto = texto or ""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sin_acentos).strip().upper()


def _clasificar_encabezado(header_norm: str) -> str | None:
    h = header_norm
    if "NOMBRE" in h and "PROVEEDOR" in h:
        return "nombre_proveedor"
    if h == "PROVEEDOR":
        return "nombre_proveedor"
    if "RFC" in h and "PROVEEDOR" in h:
        return "rfc_proveedor"
    if "NOMBRE" in h and ("DRIVER" in h or "AUX" in h):
        return "nombre_driver"
    if "CURP" in h:
        return "curp_driver"
    if "RFC" in h and ("DRIVER" in h or "AUX" in h):
        return "rfc_driver"
    if "PLACAS" in h:
        return "placas"
    if h == "ANO" or h.startswith("ANO "):
        return "anio"
    if "MARCA" in h:
        return "marca"
    if "NOMBRE" in h and "SEGURO" in h:
        return "aseguradora"
    if h == "SEGURO" or ("POLIZA" in h and "SEGURO" in h and "NUMERO" not in h):
        return "aseguradora"
    if "LICENCIA" in h:
        return "num_licencia"
    if "POLIZA" in h and "NUMERO" in h:
        return "numero_poliza"
    if "EXPIRACION" in h and "SEGURO" in h:
        return "exp_seguro"
    return None


AMARILLO_RGB = "FFFFFF00"


def _es_amarillo(celda) -> bool:
    fill = celda.fill
    color = fill.fgColor if fill else None
    return bool(color and color.type == "rgb" and color.rgb == AMARILLO_RGB)


def _fila_vacia(ws, fila: int) -> bool:
    return all(c.value in (None, "") for c in ws[fila])


def obtener_copia_de_prueba(excel_original: Path, salida: Path) -> Path:
    if not salida.exists():
        shutil.copy(excel_original, salida)
    return salida


def escribir_registro(archivo_excel: Path, hoja: str, valores: dict) -> int:
    """Agrega `valores` como un renglon nuevo en `hoja`, pero solo en las
    columnas cuyo encabezado esta resaltado en amarillo (la senal que usa
    el equipo para marcar 'esto se llena automatico'). Devuelve el numero
    de fila escrita."""
    wb = openpyxl.load_workbook(archivo_excel)
    if hoja not in wb.sheetnames:
        raise ValueError(
            f"La pestana '{hoja}' no existe. Pestanas disponibles: {', '.join(wb.sheetnames)}"
        )
    ws = wb[hoja]

    columna_por_campo: dict[str, int] = {}
    for celda in ws[1]:
        if celda.value is None or not _es_amarillo(celda):
            continue
        campo = _clasificar_encabezado(_normalizar(str(celda.value)))
        if campo and campo not in columna_por_campo:
            columna_por_campo[campo] = celda.column

    fila_destino = ws.max_row + 1
    for fila in range(2, ws.max_row + 1):
        if _fila_vacia(ws, fila):
            fila_destino = fila
            break

    for campo, valor in valores.items():
        columna = columna_por_campo.get(campo)
        if columna and valor:
            ws.cell(row=fila_destino, column=columna, value=valor)

    wb.save(archivo_excel)
    return fila_destino
