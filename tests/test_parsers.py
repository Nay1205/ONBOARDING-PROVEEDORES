"""Pruebas de las reglas de extraccion con texto de ejemplo (no son datos reales)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from extractor import parsers


class TestParsers(unittest.TestCase):
    def test_find_curp(self):
        texto = "NOMBRE: JUAN PEREZ\nCURP: GODE561231HDFNXX01\nDOMICILIO: ..."
        self.assertEqual(parsers.find_curp(texto), "GODE561231HDFNXX01")

    def test_find_curp_ausente(self):
        self.assertIsNone(parsers.find_curp("no hay nada aqui"))

    def test_find_rfc_fisica(self):
        texto = "RFC:\nPVAL800101AB1\nNombre (s): JUAN"
        self.assertEqual(parsers.find_rfc(texto, "fisica"), "PVAL800101AB1")

    def test_find_rfc_moral(self):
        texto = "RFC:\nPVA230208AA5\nDenominacion o Razon Social:\nPROYECTOS VAL-FER"
        self.assertEqual(parsers.find_rfc(texto, "moral"), "PVA230208AA5")

    def test_find_rfc_en_nombre_archivo(self):
        self.assertEqual(
            parsers.find_rfc_en_nombre_archivo("Csf_PVA230208AA5 (2).pdf"),
            "PVA230208AA5",
        )

    def test_find_razon_social(self):
        texto = "algo\nDenominación/Razón Social:\nPROYECTOS VAL-FER\notra cosa"
        self.assertEqual(parsers.find_razon_social(texto), "PROYECTOS VAL-FER")

    def test_find_aseguradora(self):
        texto = "Compañia: QUALITAS COMPANIA DE SEGUROS S.A."
        self.assertEqual(parsers.find_aseguradora(texto), "QUALITAS")

    def test_find_aseguradora_ausente(self):
        self.assertIsNone(parsers.find_aseguradora("sin datos de seguro"))

    def test_find_anio(self):
        self.assertEqual(parsers.find_anio("MODELO: 2021 MARCA: NISSAN"), "2021")

    def test_find_marca(self):
        self.assertEqual(
            parsers.find_marca("MARCA: NISSAN MODELO: 2021", parsers.MARCAS_CONOCIDAS),
            "NISSAN",
        )

    def test_find_placas_valor(self):
        self.assertEqual(parsers.find_placas("Marca: FORD Placas: ABC1234"), "ABC1234")

    def test_find_placas_na(self):
        self.assertEqual(parsers.find_placas("Modelo: 2025 Placas: NA"), "NA")

    def test_find_numero_poliza(self):
        texto = "PRA ENU ERO DE POLIZA 01974\nOtros datos"
        self.assertEqual(parsers.find_numero_poliza(texto), "01974")

    def test_find_numero_poliza_ignora_montos(self):
        texto = "Derecho de poliza $650.00\nFin de vigencia: 06/10/2026"
        self.assertIsNone(parsers.find_numero_poliza(texto))

    def test_find_numero_licencia(self):
        texto = "No. de licencia: 12345678\nOtros datos"
        self.assertEqual(parsers.find_numero_licencia(texto), "12345678")

    def test_find_expiracion_seguro(self):
        texto = "Fin de vigencia: 06/10/2026 Recargo: 0%"
        self.assertEqual(parsers.find_expiracion_seguro(texto), "06/10/2026")


if __name__ == "__main__":
    unittest.main()
