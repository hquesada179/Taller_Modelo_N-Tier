"""Pruebas de integración de CustomerService (requisito 1)."""

from negocio.domain.enums import NivelLealtad
from negocio.excepciones import CorreoDuplicadoError, ValidacionError
from tests.helpers import BaseIntegrationTest


class TestCustomerService(BaseIntegrationTest):
    def test_cliente_nuevo_inicia_como_junior_sin_puntos_ni_compras(self):
        cliente = self.crear_cliente("Grace Hopper", "grace@devcoffee.com")
        self.assertEqual(cliente.nivel_lealtad, NivelLealtad.JUNIOR)
        self.assertEqual(cliente.saldo_devpoints, 0)
        self.assertEqual(cliente.monto_acumulado_compras, 0)
        self.assertIsNotNone(cliente.id)

    def test_no_se_permite_correo_duplicado(self):
        self.crear_cliente("Grace Hopper", "grace@devcoffee.com")
        with self.assertRaises(CorreoDuplicadoError):
            self.crear_cliente("Otra Persona", "grace@devcoffee.com")

    def test_correo_invalido_es_rechazado(self):
        with self.assertRaises(ValidacionError):
            self.clientes.crear_cliente("Nombre", "correo-no-valido")


if __name__ == "__main__":
    import unittest
    unittest.main()
