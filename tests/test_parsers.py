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

    def test_find_nombre_licencia_una_linea(self):
        texto = "NO. DE LICENCIA / LICENSE ID\nJM1607861476\nNOMBRE / NAME\nJAIME CANO VAZQUEZ\nCURP"
        self.assertEqual(parsers.find_nombre_licencia(texto), "JAIME CANO VAZQUEZ")

    def test_find_nombre_licencia_dos_lineas(self):
        texto = "NOMBRE / NAME\nMIGUEL ANGEL GUTIERREZ\nRODRIGUEZ\nCURP\nGURM830927HGTTDGO6"
        self.assertEqual(parsers.find_nombre_licencia(texto), "MIGUEL ANGEL GUTIERREZ RODRIGUEZ")

    def test_find_nombre_licencia_ausente(self):
        self.assertIsNone(parsers.find_nombre_licencia("sin ninguna etiqueta util"))

    def test_derive_nombre_desde_archivo_parentesis(self):
        self.assertEqual(parsers.derive_nombre_desde_archivo("LICENCIA JAIME CANO (1).jpeg"), "JAIME CANO")

    def test_derive_nombre_desde_archivo_driver_y_numero(self):
        self.assertEqual(
            parsers.derive_nombre_desde_archivo("LICENCIA 1 DRIVER JOSE MARTIN.jpeg"),
            "JOSE MARTIN",
        )

    def test_derive_nombre_desde_archivo_guion_bajo(self):
        self.assertEqual(
            parsers.derive_nombre_desde_archivo("LICENCIA_ARMANDO BERNAL MEDINA.pdf"),
            "ARMANDO BERNAL MEDINA",
        )

    def test_find_vigencia_licencia_excluye_nacimiento(self):
        texto = "FECHA DE NACIMIENTO\n30/10/1983\nVALIDA DESDE: 04/11/2025\nVALIDA HASTA: 04/11/2027"
        self.assertEqual(parsers.find_vigencia_licencia(texto), "04/11/2027")

    def test_find_curp_candidato_validado(self):
        texto = "CURP\nCAVJ780310HGTNZMO9"
        valor, validado = parsers.find_curp_candidato(texto)
        self.assertEqual(valor, "CAVJ780310HGTNZMO9")
        self.assertTrue(validado)

    def test_find_numero_licencia_con_etiqueta_especifica(self):
        texto = "NUMERO DE LICENCIA\n000001186426\nFECHA DE NACIMIENTO"
        self.assertEqual(parsers.find_numero_licencia(texto), "000001186426")

    def test_find_numero_licencia_no_confunde_titulo(self):
        texto = "LICENCIA PARA CONDUCIR\nESTADO DE NUEVO LEON"
        self.assertIsNone(parsers.find_numero_licencia(texto))


if __name__ == "__main__":
    unittest.main()
