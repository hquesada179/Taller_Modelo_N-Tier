"""
Pruebas de integración de OrderService sobre la pila completa
(Negocio + Persistencia + SQLite real en un archivo temporal).

Cubre los requisitos 5, 6, 11, 12, 13, 15, 16 y 17 del taller.
"""

import threading

from negocio.domain.enums import EstadoPedido, NivelLealtad, TipoPedido
from negocio.excepciones import (
    PedidoPendienteExistenteError,
    StockInsuficienteError,
    TransicionEstadoInvalidaError,
)
from tests.helpers import BaseIntegrationTest


class TestOrderServiceIntegration(BaseIntegrationTest):
    # ------------------------------------------------------------
    # Requisito 16: los pedidos persisten correctamente.
    # ------------------------------------------------------------
    def test_pedido_persiste_correctamente(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(precio=6000, stock=10)

        creado = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 2}],
        )

        recuperado = self.pedidos.obtener_pedido(creado.id)
        self.assertEqual(recuperado.id, creado.id)
        self.assertEqual(recuperado.subtotal, 12_000)
        self.assertEqual(len(recuperado.items), 1)
        self.assertEqual(recuperado.items[0].cantidad, 2)
        self.assertEqual(recuperado.estado, EstadoPedido.PENDING_PAYMENT)

    # ------------------------------------------------------------
    # Requisito 11: no se permite stock insuficiente.
    # ------------------------------------------------------------
    def test_no_permite_pedido_con_stock_insuficiente(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=2)

        with self.assertRaises(StockInsuficienteError):
            self.pedidos.crear_pedido(
                cliente_id=cliente.id,
                tipo_pedido=TipoPedido.LLEVAR,
                items_solicitados=[{"producto_id": producto.id, "cantidad": 5}],
            )
        # El stock no debe haberse modificado tras el intento fallido.
        self.assertEqual(self.productos.obtener_producto(producto.id).stock_disponible, 2)

    def test_rechaza_pedido_con_producto_repetido_en_varias_lineas_que_supera_stock(self):
        """
        Regresión: dos líneas del MISMO producto (4 + 4 = 8 unidades) con
        solo 5 en inventario. Cada línea individual (4 <= 5) pasaría una
        validación ingenua por línea; la validación correcta debe agrupar
        y sumar por producto ANTES de tocar la base de datos, y rechazar
        con una excepción de negocio (no con un IntegrityError de SQLite).
        """
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=5)

        with self.assertRaises(StockInsuficienteError):
            self.pedidos.crear_pedido(
                cliente_id=cliente.id,
                tipo_pedido=TipoPedido.LLEVAR,
                items_solicitados=[
                    {"producto_id": producto.id, "cantidad": 4},
                    {"producto_id": producto.id, "cantidad": 4},
                ],
            )

        # Nada debe haberse persistido: ni el pedido ni el descuento de stock.
        self.assertEqual(self.productos.obtener_producto(producto.id).stock_disponible, 5)
        self.assertEqual(self.pedidos.listar_todos_los_pedidos(), [])
        self.assertFalse(self.pedidos.tiene_pedido_pendiente(cliente.id))

    def test_acepta_producto_repetido_en_varias_lineas_cuando_el_total_cabe_en_stock(self):
        """Caso positivo simétrico: 2 + 2 = 4 unidades con 5 en inventario debe aceptarse
        y fusionarse en una sola línea de pedido con la cantidad total."""
        cliente = self.crear_cliente()
        producto = self.crear_producto(precio=6000, stock=5)

        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[
                {"producto_id": producto.id, "cantidad": 2},
                {"producto_id": producto.id, "cantidad": 2},
            ],
        )

        self.assertEqual(len(pedido.items), 1)
        self.assertEqual(pedido.items[0].cantidad, 4)
        self.assertEqual(pedido.subtotal, 24_000)
        self.assertEqual(self.productos.obtener_producto(producto.id).stock_disponible, 1)

    # ------------------------------------------------------------
    # Requisito 12: no se permite otro pedido con uno pendiente de pago.
    # ------------------------------------------------------------
    def test_no_permite_nuevo_pedido_si_existe_uno_pendiente(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=10)

        self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )

        with self.assertRaises(PedidoPendienteExistenteError):
            self.pedidos.crear_pedido(
                cliente_id=cliente.id,
                tipo_pedido=TipoPedido.LLEVAR,
                items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
            )

    # ------------------------------------------------------------
    # Requisito 13: no se contabiliza una compra pendiente como completada.
    # ------------------------------------------------------------
    def test_pedido_pendiente_no_se_contabiliza_en_acumulado_ni_devpoints(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(precio=50_000, stock=10)

        self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )

        cliente_actual = self.clientes.obtener_cliente(cliente.id)
        self.assertEqual(cliente_actual.monto_acumulado_compras, 0)
        self.assertEqual(cliente_actual.saldo_devpoints, 0)
        self.assertEqual(cliente_actual.nivel_lealtad, NivelLealtad.JUNIOR)

    # ------------------------------------------------------------
    # Requisito 17: las transiciones de estado son válidas y secuenciales.
    # ------------------------------------------------------------
    def test_transiciones_de_estado_validas_en_secuencia(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=10)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )

        pedido = self.pedidos.cambiar_estado(pedido.id, EstadoPedido.IN_PREPARATION)
        self.assertEqual(pedido.estado, EstadoPedido.IN_PREPARATION)
        pedido = self.pedidos.cambiar_estado(pedido.id, EstadoPedido.READY)
        self.assertEqual(pedido.estado, EstadoPedido.READY)
        pedido = self.pedidos.cambiar_estado(pedido.id, EstadoPedido.DELIVERED)
        self.assertEqual(pedido.estado, EstadoPedido.DELIVERED)

    def test_no_se_permite_saltar_estados(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=10)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )
        with self.assertRaises(TransicionEstadoInvalidaError):
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.READY)

    def test_no_se_permite_retroceder_de_estado(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=10)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.IN_PREPARATION)
        with self.assertRaises(TransicionEstadoInvalidaError):
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.PENDING_PAYMENT)

    def test_no_hay_transiciones_despues_de_entregado(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(stock=10)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.IN_PREPARATION)
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.READY)
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.DELIVERED)
        with self.assertRaises(TransicionEstadoInvalidaError):
            self.pedidos.cambiar_estado(pedido.id, EstadoPedido.DELIVERED)

    # ------------------------------------------------------------
    # Requisitos 5 y 6: ascenso automático de nivel vía flujo completo.
    # ------------------------------------------------------------
    def test_ascenso_a_mid_tras_pedido_completado_de_500000_pagados(self):
        cliente = self.crear_cliente()
        # subtotal 526315 con 5% de descuento Junior -> total pagado 500000 exactos.
        producto = self.crear_producto(precio=526_315, stock=5)
        pedido = self.pedidos.crear_pedido(
            cliente_id=cliente.id,
            tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )
        self.assertEqual(pedido.total_calculado, 500_000)

        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.IN_PREPARATION)
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.READY)
        self.pedidos.cambiar_estado(pedido.id, EstadoPedido.DELIVERED)

        cliente_actual = self.clientes.obtener_cliente(cliente.id)
        self.assertEqual(cliente_actual.nivel_lealtad, NivelLealtad.MID)
        self.assertEqual(cliente_actual.monto_acumulado_compras, 500_000)

    def test_ascenso_a_senior_tras_acumular_1500000_pagados(self):
        cliente = self.crear_cliente()
        producto = self.crear_producto(precio=526_315, stock=5)
        pedido1 = self.pedidos.crear_pedido(
            cliente_id=cliente.id, tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto.id, "cantidad": 1}],
        )
        self._completar(pedido1.id)
        self.assertEqual(self.clientes.obtener_cliente(cliente.id).nivel_lealtad, NivelLealtad.MID)

        # Segundo pedido: ahora el cliente es MID (10%). Subtotal 1111111 -> total pagado 1000000.
        producto2 = self.crear_producto(nombre="Combo BugHunter", precio=1_111_111, stock=5)
        pedido2 = self.pedidos.crear_pedido(
            cliente_id=cliente.id, tipo_pedido=TipoPedido.LLEVAR,
            items_solicitados=[{"producto_id": producto2.id, "cantidad": 1}],
        )
        self.assertEqual(pedido2.total_calculado, 1_000_000)
        self._completar(pedido2.id)

        cliente_final = self.clientes.obtener_cliente(cliente.id)
        self.assertEqual(cliente_final.nivel_lealtad, NivelLealtad.SENIOR)
        self.assertEqual(cliente_final.monto_acumulado_compras, 1_500_000)

    def _completar(self, pedido_id):
        self.pedidos.cambiar_estado(pedido_id, EstadoPedido.IN_PREPARATION)
        self.pedidos.cambiar_estado(pedido_id, EstadoPedido.READY)
        self.pedidos.cambiar_estado(pedido_id, EstadoPedido.DELIVERED)

    # ------------------------------------------------------------
    # Requisito 15: el stock nunca queda negativo, incluso con pedidos
    # concurrentes compitiendo por el mismo producto.
    # ------------------------------------------------------------
    def test_stock_nunca_queda_negativo_con_pedidos_concurrentes(self):
        producto = self.crear_producto(stock=5)
        cliente_a = self.crear_cliente("Cliente A", "a@devcoffee.com")
        cliente_b = self.crear_cliente("Cliente B", "b@devcoffee.com")

        resultados = {}

        def intentar(nombre, cliente_id):
            try:
                self.pedidos.crear_pedido(
                    cliente_id=cliente_id,
                    tipo_pedido=TipoPedido.LLEVAR,
                    items_solicitados=[{"producto_id": producto.id, "cantidad": 3}],
                )
                resultados[nombre] = "OK"
            except StockInsuficienteError:
                resultados[nombre] = "RECHAZADO"

        hilo_a = threading.Thread(target=intentar, args=("A", cliente_a.id))
        hilo_b = threading.Thread(target=intentar, args=("B", cliente_b.id))
        hilo_a.start()
        hilo_b.start()
        hilo_a.join()
        hilo_b.join()

        exitos = list(resultados.values()).count("OK")
        self.assertEqual(exitos, 1, "Con stock=5 y dos pedidos de 3 unidades, solo uno puede tener éxito.")

        stock_final = self.productos.obtener_producto(producto.id).stock_disponible
        self.assertEqual(stock_final, 2)
        self.assertGreaterEqual(stock_final, 0)


if __name__ == "__main__":
    import unittest
    unittest.main()
