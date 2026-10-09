"""Implementación SQLite de ProductRepository."""

import sqlite3
from typing import List, Optional

from negocio.domain.entidades import Producto
from negocio.interfaces.repositorios import ProductRepository


def _fila_a_producto(fila: sqlite3.Row) -> Producto:
    return Producto(
        id=fila["id"],
        nombre=fila["nombre"],
        precio_base=fila["precio_base"],
        stock_disponible=fila["stock_disponible"],
        activo=bool(fila["activo"]),
    )


class SqliteProductRepository(ProductRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        fila = self._conn.execute(
            "SELECT * FROM products WHERE id = ?;", (producto_id,)
        ).fetchone()
        return _fila_a_producto(fila) if fila else None

    def listar_todos(self, solo_activos: bool = True) -> List[Producto]:
        if solo_activos:
            filas = self._conn.execute(
                "SELECT * FROM products WHERE activo = 1 ORDER BY id;"
            ).fetchall()
        else:
            filas = self._conn.execute("SELECT * FROM products ORDER BY id;").fetchall()
        return [_fila_a_producto(f) for f in filas]

    def crear(self, producto: Producto) -> Producto:
        cursor = self._conn.execute(
            """
            INSERT INTO products (nombre, precio_base, stock_disponible, activo)
            VALUES (?, ?, ?, ?);
            """,
            (producto.nombre, producto.precio_base, producto.stock_disponible, int(producto.activo)),
        )
        producto.id = cursor.lastrowid
        return producto

    def actualizar(self, producto: Producto) -> None:
        self._conn.execute(
            """
            UPDATE products
            SET nombre = ?, precio_base = ?, stock_disponible = ?, activo = ?
            WHERE id = ?;
            """,
            (producto.nombre, producto.precio_base, producto.stock_disponible, int(producto.activo), producto.id),
        )

    def ajustar_stock(self, producto_id: int, delta: int) -> None:
        self._conn.execute(
            """
            UPDATE products
            SET stock_disponible = stock_disponible + ?
            WHERE id = ?;
            """,
            (delta, producto_id),
        )
