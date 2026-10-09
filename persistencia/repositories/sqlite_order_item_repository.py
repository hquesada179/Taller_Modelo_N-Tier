"""Implementación SQLite de OrderItemRepository."""

import sqlite3
from typing import List

from negocio.domain.entidades import ElementoPedido
from negocio.interfaces.repositorios import OrderItemRepository


def _fila_a_elemento(fila: sqlite3.Row) -> ElementoPedido:
    return ElementoPedido(
        id=fila["id"],
        pedido_id=fila["pedido_id"],
        producto_id=fila["producto_id"],
        cantidad=fila["cantidad"],
        precio_unitario=fila["precio_unitario"],
        subtotal=fila["subtotal"],
    )


class SqliteOrderItemRepository(OrderItemRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def listar_por_pedido(self, pedido_id: int) -> List[ElementoPedido]:
        filas = self._conn.execute(
            "SELECT * FROM order_items WHERE pedido_id = ? ORDER BY id;", (pedido_id,)
        ).fetchall()
        return [_fila_a_elemento(f) for f in filas]

    def crear(self, elemento: ElementoPedido) -> ElementoPedido:
        cursor = self._conn.execute(
            """
            INSERT INTO order_items (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                elemento.pedido_id,
                elemento.producto_id,
                elemento.cantidad,
                elemento.precio_unitario,
                elemento.subtotal,
            ),
        )
        elemento.id = cursor.lastrowid
        return elemento
