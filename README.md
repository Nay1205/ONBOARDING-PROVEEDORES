# Extractor de datos de proveedores externos

Semana 3 (PMV) del proyecto de alta automática de proveedores: lee la
carpeta comprimida que descargas de Drive con las fotos/PDFs de un
proveedor (INE, licencia, CSF, tarjeta de circulación, póliza de
seguro, etc.), saca los datos con reglas programadas (**sin IA**, solo
OCR local + expresiones regulares) y escribe un renglón nuevo en la
pestaña del cliente correspondiente dentro del Excel de proveedores.

## Requisitos (una sola vez por computadora)

1. **Python 3.12** y **Tesseract OCR** (motor de lectura de texto en
   imágenes) — ya quedaron instalados en esta máquina.
2. Crear el entorno del proyecto e instalar las librerías:

   ```
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

## Cómo correrlo

1. Descarga de Drive el `.zip` de la carpeta del proveedor (la que
   trae las subcarpetas `DRIVER ...` y `UNIDAD`).
2. Ten a la mano el archivo `DATA OPERADORES EXTERNOS.xlsx` en esta
   misma carpeta (nunca se modifica, solo se lee).
3. Corre:

   ```
   .venv\Scripts\python.exe main.py "ruta\al\descargado.zip" --cliente "MELI 2026"
   ```

   `--cliente` es el nombre exacto de la pestaña del Excel a la que
   pertenece ese proveedor (WALMART, COPPEL, ESTAFETA, etc.).

4. El script crea (la primera vez) o reutiliza una copia de prueba
   llamada `DATA OPERADORES EXTERNOS (PRUEBA).xlsx` y ahí escribe el
   renglón nuevo. En la consola te dice qué datos encontró y cuáles
   quedaron pendientes de revisar a mano.

## Qué tan confiable es (importante)

Como no se usa IA, el sistema depende de que el texto se pueda leer
bien con OCR. Con documentos digitales limpios (como una Constancia de
Situación Fiscal) funciona muy bien. Con **fotos de celular** (INE,
tarjeta de circulación, licencia) la calidad depende mucho de la foto:
si sale borrosa, girada o con reflejo, el dato puede no encontrarse.
Por diseño, el extractor **prefiere dejar un campo vacío y avisarlo en
"Pendientes de revisar a mano"** antes que adivinar un dato incorrecto
(sobre todo en CURP, RFC y placas, donde un solo carácter mal leído
invalida el dato).

## Estructura

- `extractor/ocr.py` — lee texto de imágenes (Tesseract) y de PDFs
  (texto nativo, o OCR de respaldo si el PDF es en realidad un
  escaneo).
- `extractor/classify.py` — decide si un archivo es del proveedor, del
  driver o de la unidad, y qué tipo de documento es, según la carpeta
  y el nombre del archivo.
- `extractor/parsers.py` — expresiones regulares para CURP, RFC,
  placas, aseguradora, marca y año.
- `extractor/aggregate.py` — junta todo lo anterior en un solo
  registro por proveedor.
- `extractor/sheet_writer.py` — escribe el registro como renglón nuevo
  en la pestaña correcta del Excel.
- `main.py` — línea de comandos que conecta todo.
- `tests/test_parsers.py` — pruebas de las reglas de extracción con
  texto de ejemplo (no datos reales).

## Nota sobre datos sensibles

El `.gitignore` excluye los `.xlsx` y `.zip` a propósito: contienen
CURP, RFC, teléfonos y correos reales de personas. Solo el código se
sube al repositorio.
