"""Pruebas unitarias de StockService (requisito 11, base del requisito 15)."""

import unittest

from negocio.domain.entidades import Producto
from negocio.excepciones import CantidadInvalidaError, StockInsuficienteError
from negocio.services.stock_service import StockService


class TestStockService(unittest.TestCase):
    def setUp(self):
        self.producto = Producto(id=1, nombre="Espresso StackTrace", precio_base=6000, stock_disponible=5)

    def test_rechaza_cantidad_cero(self):
        with self.assertRaises(CantidadInvalidaError):
            StockService.validar_disponibilidad(self.producto, 0)

    def test_rechaza_cantidad_negativa(self):
        with self.assertRaises(CantidadInvalidaError):
            StockService.validar_disponibilidad(self.producto, -3)

    def test_rechaza_cantidad_mayor_al_stock_disponible(self):
        with self.assertRaises(StockInsuficienteError):
            StockService.validar_disponibilidad(self.producto, 6)

    def test_permite_cantidad_igual_al_stock_disponible(self):
        StockService.validar_disponibilidad(self.producto, 5)  # no debe lanzar


if __name__ == "__main__":
    unittest.main()
