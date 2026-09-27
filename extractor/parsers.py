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

def find_curp(text: str) -> str | None:
    upper = text.upper()
    match = CURP_RE.search(upper)
    if match:
        return match.group(0)
    return None


def find_curp_candidato(text: str) -> tuple[str | None, bool]:
    """Como find_curp, pero si el OCR quedo demasiado ruidoso para validar
    el formato exacto, regresa el mejor candidato encontrado marcado como
    'sin validar' en vez de dejarlo vacio. Devuelve (valor, validado)."""
    curp = find_curp(text)
    if curp:
        return curp, True

    # Solo se acepta un candidato "sin validar" si esta pegado a la
    # etiqueta CURP explicita: buscar cualquier bloque largo de texto sin
    # esa ancla produce puros falsos positivos (palabras vecinas pegadas).
    lineas = text.upper().splitlines()
    for i, linea in enumerate(lineas):
        if "CURP" not in linea:
            continue
        zona = (linea + lineas[i + 1] if i + 1 < len(lineas) else linea)
        zona = re.sub(r"[^A-Z0-9]", "", zona.replace("CURP", ""))
        if 16 <= len(zona) <= 19:
            return zona, False
    return None, False


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
    palabra 'PLACA', para no adivinar con cualquier texto parecido.
    Si la linea dice explicitamente 'NA' / 'N/A' (vehiculo sin placas
    todavia), se toma ese valor tal cual en lugar de dejarlo vacio."""
    for linea in text.upper().splitlines():
        if "PLACA" not in linea:
            continue
        match = PLACAS_RE.search(linea)
        if match:
            return match.group(0).replace(" ", "")
        if re.search(r"\bN\s*/?\s*A\b", linea):
            return "NA"
    return None


def find_numero_poliza(text: str) -> str | None:
    """Busca un numero junto a la palabra POLIZA, evitando montos (con '$')
    y fechas (numeros pegados a '/')."""
    for linea in text.splitlines():
        upper = linea.upper()
        if "POLIZA" not in upper and "PÓLIZA" not in upper:
            continue
        if "$" in linea:
            continue
        for match in re.finditer(r"(?<![\d/])\d{3,10}(?![\d/])", linea):
            return match.group(0)
    return None


_ETIQUETAS_NUM_LICENCIA = (
    "NUMERO DE LICENCIA", "NÚMERO DE LICENCIA", "NO. DE LICENCIA",
    "NO DE LICENCIA", "LICENSE ID", "FOLIO",
)
_CODIGO_LICENCIA_RE = re.compile(r"\b[A-Z]{0,3}\d{6,12}\b")


def find_numero_licencia(text: str) -> str | None:
    """Codigo junto a una etiqueta especifica (NUMERO DE LICENCIA, FOLIO,
    LICENSE ID...). No usa la palabra suelta 'LICENCIA' porque aparece en
    el titulo de la credencial y agarraria cualquier numero cercano."""
    lineas = text.upper().splitlines()
    for i, linea in enumerate(lineas):
        if not any(etq in linea for etq in _ETIQUETAS_NUM_LICENCIA):
            continue
        match = _CODIGO_LICENCIA_RE.search(linea)
        if not match and i + 1 < len(lineas):
            match = _CODIGO_LICENCIA_RE.search(lineas[i + 1])
        if match:
            return match.group(0)
    return None


def find_expiracion_seguro(text: str) -> str | None:
    """Fecha junto a 'FIN DE VIGENCIA' (o 'VIGENCIA' si no hay otra pista)."""
    lineas = text.splitlines()
    for i, linea in enumerate(lineas):
        upper = linea.upper()
        if "FIN" in upper and "VIGENCIA" in upper:
            match = FECHA_RE.search(linea) or (
                FECHA_RE.search(lineas[i + 1]) if i + 1 < len(lineas) else None
            )
            if match:
                return match.group(0)
    return None


_ETIQUETAS_NOMBRE = ("NOMBRE", "NAME")
_ETIQUETAS_CORTE_NOMBRE = (
    "CURP", "DOMICILIO", "ADDRESS", "EXPEDIC", "VIGENC", "FOLIO",
    "LICENCIA", "NACIMIENTO", "TIPO", "CLASS", "ANTIGUEDAD",
)


def find_nombre_licencia(text: str) -> str | None:
    """Nombre justo despues de una etiqueta NOMBRE/NAME. Puede venir en 1 o
    2 lineas seguidas, hasta toparse con la siguiente etiqueta del formato."""
    lineas = text.splitlines()
    for i, linea in enumerate(lineas):
        upper = linea.upper()
        if not any(etq in upper for etq in _ETIQUETAS_NOMBRE):
            continue
        partes = []
        for candidata in lineas[i + 1 : i + 4]:
            cand_upper = candidata.upper()
            if not candidata.strip():
                break
            if any(corte in cand_upper for corte in _ETIQUETAS_CORTE_NOMBRE):
                break
            if any(c.isdigit() for c in candidata):
                break
            letras = re.sub(r"[^A-ZÑ ]", "", cand_upper).strip()
            if len(letras) < 2:
                break
            partes.append(letras)
        if partes:
            return " ".join(partes)
    return None


def derive_nombre_desde_archivo(nombre_archivo: str) -> str:
    """Deriva el nombre de la persona a partir del nombre del archivo,
    ej. 'LICENCIA_JAIME CANO (1).jpeg' -> 'JAIME CANO'. Sirve como
    respaldo cuando el formato de la licencia no trae una etiqueta NOMBRE
    clara para anclar el OCR."""
    base = re.sub(r"\.[A-Za-z0-9]+$", "", nombre_archivo).upper()
    base = re.sub(r"^LICEN+CIA[_\s]*", "", base)
    base = re.sub(r"\bDRIVER\b", " ", base)
    base = re.sub(r"\(\d+\)", " ", base)
    base = re.sub(r"\b\d+\b", " ", base)
    base = base.replace("_", " ")
    return re.sub(r"\s+", " ", base).strip()


def find_vigencia_licencia(text: str) -> str | None:
    """La fecha de vigencia/expiracion es, en cualquier formato de estado,
    la fecha mas lejana en el futuro impresa en la credencial (la de
    expedicion y la de nacimiento siempre son anteriores). Se excluye la
    fecha pegada a la etiqueta de nacimiento para no confundirla."""
    lineas = text.upper().splitlines()
    excluidas = set()
    for i, linea in enumerate(lineas):
        if "NACIMIENTO" in linea:
            excluidas.add(i)
            excluidas.add(i + 1)

    fechas = []
    for i, linea in enumerate(lineas):
        if i in excluidas:
            continue
        fechas.extend(m.group(0) for m in FECHA_RE.finditer(linea))
    if not fechas:
        return None

    def anio_de(fecha: str) -> int:
        anio = re.split(r"[/\-.]", fecha)[2]
        return int(anio) + 2000 if len(anio) == 2 else int(anio)

    return max(fechas, key=anio_de)


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
