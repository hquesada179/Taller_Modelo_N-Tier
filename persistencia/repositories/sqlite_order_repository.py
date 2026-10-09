"""Implementación SQLite de OrderRepository."""

import sqlite3
from typing import List, Optional

from negocio.domain.entidades import Pedido
from negocio.domain.enums import EstadoPedido, TipoPedido
from negocio.interfaces.repositorios import OrderRepository
from persistencia.repositories.sqlite_order_item_repository import SqliteOrderItemRepository


def _fila_a_pedido(fila: sqlite3.Row, items=None) -> Pedido:
    return Pedido(
        id=fila["id"],
        cliente_id=fila["cliente_id"],
        fecha=fila["fecha"],
        estado=EstadoPedido(fila["estado"]),
        subtotal=fila["subtotal"],
        descuento_nivel=fila["descuento_nivel"],
        descuento_devpoints=fila["descuento_devpoints"],
        total_calculado=fila["total_calculado"],
        devpoints_redimidos=fila["devpoints_redimidos"],
        devpoints_otorgados=fila["devpoints_otorgados"],
        beneficios_aplicados=bool(fila["beneficios_aplicados"]),
        tipo_pedido=TipoPedido(fila["tipo_pedido"]),
        numero_mesa=fila["numero_mesa"],
        items=items or [],
    )


class SqliteOrderRepository(OrderRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._items_repo = SqliteOrderItemRepository(conn)

    def obtener_por_id(self, pedido_id: int) -> Optional[Pedido]:
        fila = self._conn.execute("SELECT * FROM orders WHERE id = ?;", (pedido_id,)).fetchone()
        if not fila:
            return None
        items = self._items_repo.listar_por_pedido(pedido_id)
        return _fila_a_pedido(fila, items)

    def listar_por_cliente(self, cliente_id: int) -> List[Pedido]:
        filas = self._conn.execute(
            "SELECT * FROM orders WHERE cliente_id = ? ORDER BY id DESC;", (cliente_id,)
        ).fetchall()
        return [_fila_a_pedido(f, self._items_repo.listar_por_pedido(f["id"])) for f in filas]

    def listar_todos(self) -> List[Pedido]:
        filas = self._conn.execute("SELECT * FROM orders ORDER BY id DESC;").fetchall()
        return [_fila_a_pedido(f, self._items_repo.listar_por_pedido(f["id"])) for f in filas]

    def existe_pendiente_de_pago(self, cliente_id: int) -> bool:
        fila = self._conn.execute(
            """
            SELECT 1 FROM orders
            WHERE cliente_id = ? AND estado = ?
            LIMIT 1;
            """,
            (cliente_id, EstadoPedido.PENDING_PAYMENT.value),
        ).fetchone()
        return fila is not None

    def crear(self, pedido: Pedido) -> Pedido:
        cursor = self._conn.execute(
            """
            INSERT INTO orders (
                cliente_id, estado, subtotal, descuento_nivel, descuento_devpoints,
                total_calculado, devpoints_redimidos, devpoints_otorgados,
                beneficios_aplicados, tipo_pedido, numero_mesa
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                pedido.cliente_id,
                pedido.estado.value,
                pedido.subtotal,
                pedido.descuento_nivel,
                pedido.descuento_devpoints,
                pedido.total_calculado,
                pedido.devpoints_redimidos,
                pedido.devpoints_otorgados,
                int(pedido.beneficios_aplicados),
                pedido.tipo_pedido.value,
                pedido.numero_mesa,
            ),
        )
        pedido.id = cursor.lastrowid
        fila = self._conn.execute(
            "SELECT fecha FROM orders WHERE id = ?;", (pedido.id,)
        ).fetchone()
        pedido.fecha = fila["fecha"]
        return pedido

    def actualizar_estado(self, pedido_id: int, nuevo_estado: EstadoPedido) -> None:
        self._conn.execute(
            "UPDATE orders SET estado = ? WHERE id = ?;",
            (nuevo_estado.value, pedido_id),
        )

    def actualizar_totales_y_beneficios(self, pedido: Pedido) -> None:
        self._conn.execute(
            """
            UPDATE orders
            SET subtotal = ?, descuento_nivel = ?, descuento_devpoints = ?,
                total_calculado = ?, devpoints_redimidos = ?, devpoints_otorgados = ?,
                beneficios_aplicados = ?
            WHERE id = ?;
            """,
            (
                pedido.subtotal,
                pedido.descuento_nivel,
                pedido.descuento_devpoints,
                pedido.total_calculado,
                pedido.devpoints_redimidos,
                pedido.devpoints_otorgados,
                int(pedido.beneficios_aplicados),
                pedido.id,
            ),
        )
