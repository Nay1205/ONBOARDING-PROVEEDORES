"""Clasifica cada archivo de la carpeta del proveedor segun en que
subcarpeta esta (proveedor / driver / unidad) y que tipo de documento es,
usando solo el nombre de carpeta y archivo (sin IA)."""
from dataclasses import dataclass
from pathlib import Path

DOC_KEYWORDS = [
    ("CSF", ["csf"]),
    ("INE", ["ine", "ife"]),
    ("LICENCIA", ["licen"]),
    ("TARJETA_CIRCULACION", ["tarjeta", "circulac"]),
    ("SEGURO", ["seguro", "poliza", "póliza"]),
    ("GAFETE", ["gafete"]),
    ("CUENTA_BANCARIA", ["cuenta", "banc"]),
    ("FOTO_UNIDAD", ["frente", "posterior", "izquierdo", "derecho"]),
]


@dataclass
class ClasificacionArchivo:
    ruta: Path
    zona: str  # "proveedor" | "driver" | "unidad"
    tipo_doc: str
    nombre_carpeta_driver: str | None = None


def _match_doc_type(filename_lower: str) -> str:
    for tipo, keywords in DOC_KEYWORDS:
        if any(kw in filename_lower for kw in keywords):
            return tipo
    return "OTRO"


def classify_file(path: Path, root: Path) -> ClasificacionArchivo:
    rel_parts = path.relative_to(root).parts
    filename_lower = path.name.lower()
    tipo_doc = _match_doc_type(filename_lower)

    zona = "proveedor"
    nombre_carpeta_driver = None
    for part in rel_parts[:-1]:  # carpetas intermedias, sin el nombre de archivo
        part_upper = part.strip().upper()
        if part_upper.startswith("DRIVER"):
            zona = "driver"
            nombre_carpeta_driver = part.strip()[len("DRIVER"):].strip()
        elif part_upper.startswith("UNIDAD"):
            zona = "unidad"

    return ClasificacionArchivo(
        ruta=path,
        zona=zona,
        tipo_doc=tipo_doc,
        nombre_carpeta_driver=nombre_carpeta_driver,
    )
