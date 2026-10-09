"""Pruebas de integración de ProductService (apoyo del requisito 15)."""

from negocio.excepciones import ValidacionError
from tests.helpers import BaseIntegrationTest


class TestProductService(BaseIntegrationTest):
    def test_crear_y_listar_producto(self):
        self.crear_producto("Latte NullPointer", 8500, 20)
        productos = self.productos.listar_productos()
        self.assertEqual(len(productos), 1)
        self.assertEqual(productos[0].nombre, "Latte NullPointer")
        self.assertEqual(productos[0].stock_disponible, 20)

    def test_ajuste_de_inventario_no_permite_stock_negativo(self):
        producto = self.crear_producto(stock=3)
        with self.assertRaises(ValidacionError):
            self.productos.ajustar_inventario(producto.id, -5)

    def test_ajuste_de_inventario_positivo_incrementa_stock(self):
        producto = self.crear_producto(stock=3)
        actualizado = self.productos.ajustar_inventario(producto.id, 10)
        self.assertEqual(actualizado.stock_disponible, 13)


if __name__ == "__main__":
    import unittest
    unittest.main()
