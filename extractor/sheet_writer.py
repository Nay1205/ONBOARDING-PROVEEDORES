"""Escribe un registro extraido como renglon nuevo en la pestana del
cliente correspondiente, dentro del archivo de Excel de proveedores.
"""
import re
import shutil
import unicodedata
from datetime import date
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
    if "COMENTARIOS" in h or "COMETARIOS" in h:
        return "comentarios"
    if "CAPTURO" in h:
        return "capturo"
    if "FECHA" in h and "INGRESO" in h:
        return "fecha_ingreso"
    return None


def _fila_vacia(ws, fila: int) -> bool:
    return all(c.value in (None, "") for c in ws[fila])


def obtener_copia_de_prueba(excel_original: Path, salida: Path) -> Path:
    if not salida.exists():
        shutil.copy(excel_original, salida)
    return salida


def escribir_registro(
    archivo_excel: Path,
    hoja: str,
    valores: dict,
    pendientes: list[str],
) -> int:
    """Agrega `valores` como un renglon nuevo en `hoja`. Devuelve el numero de fila escrita."""
    wb = openpyxl.load_workbook(archivo_excel)
    if hoja not in wb.sheetnames:
        raise ValueError(
            f"La pestana '{hoja}' no existe. Pestanas disponibles: {', '.join(wb.sheetnames)}"
        )
    ws = wb[hoja]

    columna_por_campo: dict[str, int] = {}
    for celda in ws[1]:
        if celda.value is None:
            continue
        campo = _clasificar_encabezado(_normalizar(str(celda.value)))
        if campo and campo not in columna_por_campo:
            columna_por_campo[campo] = celda.column

    fila_destino = ws.max_row + 1
    for fila in range(2, ws.max_row + 1):
        if _fila_vacia(ws, fila):
            fila_destino = fila
            break

    datos_a_escribir = dict(valores)
    datos_a_escribir.setdefault("fecha_ingreso", date.today().strftime("%d/%m/%Y"))
    datos_a_escribir.setdefault("capturo", "EXTRACTOR AUTOMATICO")
    if pendientes:
        datos_a_escribir.setdefault(
            "comentarios", "Revisar: " + "; ".join(pendientes)
        )

    for campo, valor in datos_a_escribir.items():
        columna = columna_por_campo.get(campo)
        if columna and valor:
            ws.cell(row=fila_destino, column=columna, value=valor)

    wb.save(archivo_excel)
    return fila_destino
