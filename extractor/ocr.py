"""Lectura de texto de imagenes y PDFs sin usar IA: OCR local (Tesseract)
para fotos, y texto nativo de PDF con respaldo por OCR cuando el PDF es
en realidad una imagen escaneada.
"""
import io
import shutil
from pathlib import Path

import fitz  # pymupdf
import pytesseract
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
LANG = "spa+eng"

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    str(Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
]


def configure_tesseract() -> None:
    if shutil.which("tesseract"):
        return
    for candidate in _TESSERACT_CANDIDATES:
        if Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            return
    raise RuntimeError(
        "No se encontro Tesseract OCR instalado. Instalalo desde "
        "https://github.com/UB-Mannheim/tesseract/releases"
    )


def _text_quality(text: str) -> float:
    """Que tan 'usable' se ve un texto: proporcion de caracteres alfanumericos."""
    if not text:
        return 0.0
    alnum = sum(c.isalnum() for c in text)
    return alnum / max(len(text), 1)


def ocr_image(path: Path) -> str:
    with Image.open(path) as img:
        return pytesseract.image_to_string(img, lang=LANG, config="--psm 6")


def _ocr_pdf_pages(doc: "fitz.Document") -> str:
    chunks = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        chunks.append(pytesseract.image_to_string(img, lang=LANG, config="--psm 6"))
    return "\n".join(chunks)


def extract_pdf_text(path: Path) -> str:
    with fitz.open(path) as doc:
        native = "\n".join(page.get_text() for page in doc)
        if _text_quality(native) > 0.35 and len(native.strip()) > 40:
            return native
        ocr_text = _ocr_pdf_pages(doc)
        return ocr_text if _text_quality(ocr_text) >= _text_quality(native) else native


def extract_text(path: Path) -> str:
    """Punto de entrada unico: devuelve el mejor texto disponible para un archivo."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf_text(path)
    if ext in IMAGE_EXTS:
        return ocr_image(path)
    return ""
