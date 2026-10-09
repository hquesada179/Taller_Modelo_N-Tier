"""Pruebas unitarias de DiscountService (requisitos 2, 3 y 4 del taller)."""

import unittest

from negocio.domain.enums import NivelLealtad
from negocio.services.discount_service import DiscountService


class TestDiscountService(unittest.TestCase):
    def test_junior_recibe_5_por_ciento(self):
        descuento = DiscountService.calcular_descuento_nivel(NivelLealtad.JUNIOR, 100_000)
        self.assertEqual(descuento, 5_000)

    def test_mid_recibe_10_por_ciento(self):
        descuento = DiscountService.calcular_descuento_nivel(NivelLealtad.MID, 100_000)
        self.assertEqual(descuento, 10_000)

    def test_senior_recibe_15_por_ciento(self):
        descuento = DiscountService.calcular_descuento_nivel(NivelLealtad.SENIOR, 100_000)
        self.assertEqual(descuento, 15_000)

    def test_calcular_totales_no_permite_descuento_devpoints_mayor_al_restante(self):
        resultado = DiscountService.calcular_totales(
            subtotal=10_000, nivel=NivelLealtad.JUNIOR, descuento_devpoints=50_000
        )
        # subtotal 10000, descuento_nivel 500 (5%), restante 9500.
        # el descuento de devpoints solicitado (50000) se recorta al restante.
        self.assertEqual(resultado["descuento_nivel"], 500)
        self.assertEqual(resultado["descuento_devpoints"], 9_500)
        self.assertEqual(resultado["total_calculado"], 0)

    def test_total_calculado_nunca_es_negativo(self):
        resultado = DiscountService.calcular_totales(
            subtotal=1_000, nivel=NivelLealtad.SENIOR, descuento_devpoints=10_000
        )
        self.assertGreaterEqual(resultado["total_calculado"], 0)


if __name__ == "__main__":
    unittest.main()
