"""Prueba de integración de redención de DevPoints a través de OrderService."""

from negocio.domain.enums import EstadoPedido, TipoPedido
from negocio.excepciones import RedencionInvalidaError
from tests.helpers import BaseIntegrationTest


class TestRedencionDevPointsIntegracion(BaseIntegrationTest):
    def _dar_puntos_al_cliente(self, cliente_id, puntos):
        """Completa un pedido barato repetidas veces hasta otorgar `puntos` DevPoints."""
        # precio_base 21100 con 5% de descuento Junior -> total pagado 20045
        # (dentro de [20000, 39999): otorga exactamente 1 DevPoint por pedido).
        producto = self.crear_producto(nombre="Galleta Byte-Size", precio=21_100, stock=1000)
        for _ in range(puntos):
            pedido = self.pedidos.crear_pedido(
                cliente_id=cliente_id, tipo_pedido=TipoPedido.LLEVAR,
                items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
            )
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.IN_PREPARATION)
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.READY)
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.DELIVERED)

    def test_redimir_puntos_reduce_el_total_y_el_saldo_inmediatamente(self):
        cliente = self.crear_cliente()
        self._dar_puntos_al_cliente(cliente.id, puntos=10)  # 10 DevPoints = $2.000

        producto = self.crear_producto(nombre="Americano SegFault", precio=10_000, stock=10)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id, tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
            puntos_a_redimir=5,
        )
        # subtotal 10000, descuento_nivel Junior 5% = 500, descuento_devpoints 5*200=1000
        self.assertEqual(pedido.descuento_devpoints, 1_000)
        self.assertEqual(pedido.total_calculado, 10_000 - 500 - 1_000)

        cliente_actual = self.clientes.obtener_cliente(cliente.id)
        self.assertEqual(cliente_actual.saldo_devpoints, 5)  # 10 - 5 redimidos

    def test_no_se_puede_redimir_mas_puntos_de_los_disponibles(self):
        cliente = self.crear_cliente()
        self._dar_puntos_al_cliente(cliente.id, puntos=2)

        producto = self.crear_producto(precio=50_000, stock=10)
        with self.assertRaises(RedencionInvalidaError):
            self.pedidos.crear_pedido(
                cliente_id=cliente.id, tipo_pedido=TipoPedido.LLEVAR,
                items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
                puntos_a_redimir=3,
            )


if __name__ == "__main__":
    import unittest
    unittest.main()
