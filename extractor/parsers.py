"""Reglas programadas (sin IA) para sacar datos estructurados del texto
que ya salio del OCR / del PDF. Todo por expresiones regulares y listas
de palabras clave.
"""
import re

_ESTADOS_CURP = (
    "AS|BC|BS|CC|CS|CH|CL|CM|DF|CX|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|"
    "QO|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE"
)

CURP_RE = re.compile(
    rf"[A-Z][AEIOUX][A-Z]{{2}}\d{{2}}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"
    rf"[HM](?:{_ESTADOS_CURP})[B-DF-HJ-NP-TV-Z]{{3}}[A-Z0-9]\d"
)
RFC_MORAL_RE = re.compile(r"[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}")
RFC_FISICA_RE = re.compile(r"[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}")
PLACAS_RE = re.compile(r"\b[A-Z]{2,3}[- ]?\d{2,4}[- ]?[A-Z]{0,2}\b")
ANIO_RE = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
FECHA_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2}|[A-Z]{3})[/\-.](\d{4}|\d{2})\b")

# Marcas que solo venden seguros: si aparecen en el texto, es la aseguradora.
ASEGURADORAS_EXCLUSIVAS = [
    "QUALITAS", "GNP", "AXA", "HDI", "MAPFRE", "ANA SEGUROS", "CHUBB",
    "ATLAS", "ZURICH", "SURA", "EL POTOSI", "PRIMERO SEGUROS",
    "ABA SEGUROS", "GENERAL DE SEGUROS", "PLAN SEGURO",
]
# Grupos financieros que venden seguros PERO tambien son bancos: solo cuentan
# si aparecen junto a la palabra "SEGUROS" (si no, es solo el banco acreedor).
ASEGURADORAS_AMBIGUAS = ["BANORTE", "INBURSA", "AFIRME", "MULTIVA"]

_MESES = {
    "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05",
    "JUN": "06", "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10",
    "NOV": "11", "DIC": "12",
}


def find_curp(text: str) -> str | None:
    upper = text.upper()
    match = CURP_RE.search(upper)
    if match:
        return match.group(0)
    return None


def find_rfc(text: str, persona: str = "fisica") -> str | None:
    upper = text.upper()
    pattern = RFC_FISICA_RE if persona == "fisica" else RFC_MORAL_RE
    match = pattern.search(upper)
    return match.group(0) if match else None


def find_rfc_en_nombre_archivo(filename: str) -> str | None:
    """Muchos CSF se descargan como 'Csf_<RFC>.pdf'; es una pista confiable."""
    upper = filename.upper()
    match = RFC_FISICA_RE.search(upper) or RFC_MORAL_RE.search(upper)
    return match.group(0) if match else None


def find_razon_social(text: str) -> str | None:
    """Busca la linea que sigue a 'Denominacion/Razon Social' en una CSF."""
    lines = [l.strip() for l in text.splitlines()]
    for i, line in enumerate(lines):
        norm = line.upper()
        if "RAZ" in norm and "SOCIAL" in norm:
            for candidate in lines[i + 1 : i + 3]:
                if candidate and len(candidate) > 2:
                    return candidate
    return None


def find_placas(text: str) -> str | None:
    """Solo acepta una coincidencia si esta en la misma linea que la
    palabra 'PLACA', para no adivinar con cualquier texto parecido."""
    for linea in text.upper().splitlines():
        if "PLACA" not in linea:
            continue
        match = PLACAS_RE.search(linea)
        if match:
            return match.group(0).replace(" ", "")
    return None


def find_anio(text: str) -> str | None:
    match = ANIO_RE.search(text)
    return match.group(0) if match else None


def find_aseguradora(text: str) -> str | None:
    upper = text.upper()
    for nombre in ASEGURADORAS_EXCLUSIVAS:
        if nombre in upper:
            return nombre
    for nombre in ASEGURADORAS_AMBIGUAS:
        if f"SEGUROS {nombre}" in upper or f"{nombre} SEGUROS" in upper:
            return nombre
    return None


def find_marca(text: str, marcas_conocidas: list[str]) -> str | None:
    upper = text.upper()
    for marca in marcas_conocidas:
        if marca in upper:
            return marca
    return None


MARCAS_CONOCIDAS = [
    "NISSAN", "CHEVROLET", "FORD", "VOLKSWAGEN", "TOYOTA", "HONDA",
    "GENERAL MOTORS", "GMC", "RENAULT", "KIA", "HYUNDAI", "MAZDA",
    "DODGE", "RAM", "FIAT", "SUZUKI", "MITSUBISHI", "SEAT", "PEUGEOT",
    "ISUZU", "FREIGHTLINER", "INTERNATIONAL", "JAC",
]
