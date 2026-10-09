"""
Pruebas unitarias de LoyaltyService (requisitos 7, 8, 9, 10, 14 y el
ascenso automático de nivel, requisitos 5 y 6, a nivel de cálculo puro).
"""

import unittest

from negocio.domain.entidades import Cliente, Pedido
from negocio.domain.enums import EstadoPedido, NivelLealtad, TipoPedido
from negocio.excepciones import RedencionInvalidaError
from negocio.services.loyalty_service import LoyaltyService


def _cliente(nivel=NivelLealtad.JUNIOR, saldo=0, acumulado=0):
    return Cliente(
        id=1, nombre="Test", correo="test@test.devcoffee",
        nivel_lealtad=nivel, saldo_devpoints=saldo, monto_acumulado_compras=acumulado,
    )


def _pedido(total_calculado, beneficios_aplicados=False):
    return Pedido(
        id=1, cliente_id=1, fecha="2026-01-01", estado=EstadoPedido.DELIVERED,
        subtotal=total_calculado, descuento_nivel=0, descuento_devpoints=0,
        total_calculado=total_calculado, devpoints_redimidos=0, devpoints_otorgados=0,
        beneficios_aplicados=beneficios_aplicados, tipo_pedido=TipoPedido.LLEVAR,
    )


class TestLoyaltyService(unittest.TestCase):
    def test_pedido_de_20000_otorga_1_devpoint(self):
        self.assertEqual(LoyaltyService.calcular_puntos_otorgados(20_000), 1)

    def test_pedido_de_40000_otorga_2_devpoints(self):
        self.assertEqual(LoyaltyService.calcular_puntos_otorgados(40_000), 2)

    def test_redencion_de_5_puntos_equivale_a_1000_pesos(self):
        self.assertEqual(LoyaltyService.valor_en_pesos(5), 1_000)

    def test_no_se_pueden_redimir_mas_puntos_que_los_disponibles(self):
        cliente = _cliente(saldo=3)
        with self.assertRaises(RedencionInvalidaError):
            LoyaltyService.validar_redencion(cliente, 4, total_elegible=10_000)

    def test_no_se_pueden_redimir_puntos_negativos(self):
        cliente = _cliente(saldo=10)
        with self.assertRaises(RedencionInvalidaError):
            LoyaltyService.validar_redencion(cliente, -1, total_elegible=10_000)

    def test_redencion_no_puede_superar_el_total_elegible(self):
        cliente = _cliente(saldo=100)  # 100 puntos = $20.000, pero el pedido vale menos
        with self.assertRaises(RedencionInvalidaError):
            LoyaltyService.validar_redencion(cliente, 100, total_elegible=5_000)

    def test_redencion_valida_no_lanza_error(self):
        cliente = _cliente(saldo=10)
        LoyaltyService.validar_redencion(cliente, 5, total_elegible=5_000)  # no debe lanzar

    def test_cliente_asciende_a_mid_al_llegar_a_500000(self):
        cliente = _cliente(nivel=NivelLealtad.JUNIOR, acumulado=0)
        pedido = _pedido(total_calculado=500_000)
        LoyaltyService.aplicar_beneficios_pedido_completado(cliente, pedido)
        self.assertEqual(cliente.nivel_lealtad, NivelLealtad.MID)
        self.assertEqual(cliente.monto_acumulado_compras, 500_000)

    def test_cliente_asciende_a_senior_al_llegar_a_1500000(self):
        cliente = _cliente(nivel=NivelLealtad.MID, acumulado=500_000)
        pedido = _pedido(total_calculado=1_000_000)
        LoyaltyService.aplicar_beneficios_pedido_completado(cliente, pedido)
        self.assertEqual(cliente.nivel_lealtad, NivelLealtad.SENIOR)
        self.assertEqual(cliente.monto_acumulado_compras, 1_500_000)

    def test_el_nivel_nunca_desciende(self):
        cliente = _cliente(nivel=NivelLealtad.SENIOR, acumulado=2_000_000)
        nuevo_nivel = LoyaltyService.evaluar_nivel(0, cliente.nivel_lealtad)
        self.assertEqual(nuevo_nivel, NivelLealtad.SENIOR)

    def test_los_beneficios_no_se_aplican_duplicadamente(self):
        cliente = _cliente(nivel=NivelLealtad.JUNIOR, acumulado=0, saldo=0)
        pedido = _pedido(total_calculado=40_000)

        LoyaltyService.aplicar_beneficios_pedido_completado(cliente, pedido)
        self.assertEqual(cliente.saldo_devpoints, 2)
        self.assertEqual(cliente.monto_acumulado_compras, 40_000)
        self.assertTrue(pedido.beneficios_aplicados)

        # Un segundo intento sobre el mismo pedido no debe duplicar nada.
        LoyaltyService.aplicar_beneficios_pedido_completado(cliente, pedido)
        self.assertEqual(cliente.saldo_devpoints, 2)
        self.assertEqual(cliente.monto_acumulado_compras, 40_000)


if __name__ == "__main__":
    unittest.main()
