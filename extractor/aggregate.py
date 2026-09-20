"""Recorre la carpeta de un proveedor, junta el texto de cada documento
por zona (proveedor / driver / unidad) y arma un solo registro con los
campos que se pudieron sacar, mas la lista de lo que falta revisar a mano.
"""
from dataclasses import dataclass, field
from pathlib import Path

from . import ocr, parsers
from .classify import classify_file

IGNORAR_EXTENSIONES = {".ds_store", ".ini"}


@dataclass
class ResultadoExtraccion:
    valores: dict = field(default_factory=dict)
    pendientes: list = field(default_factory=list)
    archivos_procesados: list = field(default_factory=list)
    debug_textos: dict = field(default_factory=dict)


def _iter_archivos(carpeta: Path):
    for path in sorted(carpeta.rglob("*")):
        if path.is_file() and path.suffix.lower() not in IGNORAR_EXTENSIONES:
            yield path


def procesar_carpeta_proveedor(carpeta: Path) -> ResultadoExtraccion:
    ocr.configure_tesseract()
    resultado = ResultadoExtraccion()

    texto_por_zona = {"proveedor": [], "driver": [], "unidad": []}
    nombre_driver_carpeta = None

    for path in _iter_archivos(carpeta):
        clasif = classify_file(path, carpeta)
        try:
            texto = ocr.extract_text(path)
        except Exception as exc:  # documento ilegible: se anota y se sigue
            resultado.pendientes.append(f"No se pudo leer '{path.name}': {exc}")
            continue

        resultado.archivos_procesados.append(str(path.relative_to(carpeta)))
        resultado.debug_textos[str(path.relative_to(carpeta))] = texto
        texto_por_zona[clasif.zona].append((clasif.tipo_doc, texto, path.name))
        if clasif.nombre_carpeta_driver:
            nombre_driver_carpeta = clasif.nombre_carpeta_driver

    valores = resultado.valores

    # --- Proveedor (persona/empresa que contrata) ---
    for tipo, texto, filename in texto_por_zona["proveedor"]:
        if tipo == "CSF":
            valores.setdefault("nombre_proveedor", parsers.find_razon_social(texto))
            valores.setdefault(
                "rfc_proveedor",
                parsers.find_rfc(texto, "moral")
                or parsers.find_rfc(texto, "fisica")
                or parsers.find_rfc_en_nombre_archivo(filename),
            )

    # --- Driver (persona que opera la unidad) ---
    if nombre_driver_carpeta:
        valores["nombre_driver"] = nombre_driver_carpeta
    for tipo, texto, filename in texto_por_zona["driver"]:
        if tipo in ("INE", "LICENCIA"):
            valores.setdefault("curp_driver", parsers.find_curp(texto))
        if tipo == "LICENCIA":
            valores.setdefault("num_licencia", parsers.find_numero_licencia(texto))
        if tipo == "CSF":
            valores.setdefault("rfc_driver", parsers.find_rfc(texto, "fisica"))

    # --- Unidad (vehiculo) ---
    for tipo, texto, filename in texto_por_zona["unidad"]:
        if tipo == "TARJETA_CIRCULACION":
            valores.setdefault("placas", parsers.find_placas(texto))
            valores.setdefault("anio", parsers.find_anio(texto))
            valores.setdefault("marca", parsers.find_marca(texto, parsers.MARCAS_CONOCIDAS))
        if tipo == "SEGURO":
            valores.setdefault("aseguradora", parsers.find_aseguradora(texto))
            valores.setdefault("numero_poliza", parsers.find_numero_poliza(texto))
            valores.setdefault("exp_seguro", parsers.find_expiracion_seguro(texto))
            if valores.get("placas") is None:
                valores["placas"] = parsers.find_placas(texto)

    campos_esperados = [
        "nombre_proveedor", "rfc_proveedor", "nombre_driver", "curp_driver",
        "rfc_driver", "num_licencia", "placas", "anio", "marca",
        "aseguradora", "numero_poliza", "exp_seguro",
    ]
    for campo in campos_esperados:
        if not valores.get(campo):
            resultado.pendientes.append(f"Falta '{campo}': revisar a mano")

    return resultado
