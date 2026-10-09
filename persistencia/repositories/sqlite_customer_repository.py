"""
Implementación SQLite de CustomerRepository.

Responsabilidad exclusiva: ejecutar SQL y mapear filas a entidades de
dominio. No decide niveles de lealtad ni reglas de negocio.
"""

import sqlite3
from typing import List, Optional

from negocio.domain.entidades import Cliente
from negocio.domain.enums import NivelLealtad
from negocio.interfaces.repositorios import CustomerRepository


def _fila_a_cliente(fila: sqlite3.Row) -> Cliente:
    return Cliente(
        id=fila["id"],
        nombre=fila["nombre"],
        correo=fila["correo"],
        nivel_lealtad=NivelLealtad(fila["nivel_lealtad"]),
        saldo_devpoints=fila["saldo_devpoints"],
        monto_acumulado_compras=fila["monto_acumulado_compras"],
    )


class SqliteCustomerRepository(CustomerRepository):
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        fila = self._conn.execute(
            "SELECT * FROM customers WHERE id = ?;", (cliente_id,)
        ).fetchone()
        return _fila_a_cliente(fila) if fila else None

    def obtener_por_correo(self, correo: str) -> Optional[Cliente]:
        fila = self._conn.execute(
            "SELECT * FROM customers WHERE correo = ?;", (correo,)
        ).fetchone()
        return _fila_a_cliente(fila) if fila else None

    def listar_todos(self) -> List[Cliente]:
        filas = self._conn.execute("SELECT * FROM customers ORDER BY id;").fetchall()
        return [_fila_a_cliente(f) for f in filas]

    def crear(self, cliente: Cliente) -> Cliente:
        cursor = self._conn.execute(
            """
            INSERT INTO customers (nombre, correo, nivel_lealtad, saldo_devpoints, monto_acumulado_compras)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                cliente.nombre,
                cliente.correo,
                cliente.nivel_lealtad.value,
                cliente.saldo_devpoints,
                cliente.monto_acumulado_compras,
            ),
        )
        cliente.id = cursor.lastrowid
        return cliente

    def actualizar(self, cliente: Cliente) -> None:
        self._conn.execute(
            """
            UPDATE customers
            SET nombre = ?, correo = ?, nivel_lealtad = ?, saldo_devpoints = ?,
                monto_acumulado_compras = ?
            WHERE id = ?;
            """,
            (
                cliente.nombre,
                cliente.correo,
                cliente.nivel_lealtad.value,
                cliente.saldo_devpoints,
                cliente.monto_acumulado_compras,
                cliente.id,
            ),
        )
