"""
Unidad de trabajo (Unit of Work) sobre SQLite.

Abre una conexión, inicia una transacción ("BEGIN IMMEDIATE") al entrar
en el bloque `with` y confirma (COMMIT) o revierte (ROLLBACK) al salir,
garantizando que las operaciones de stock y pedidos sean atómicas y
protegiéndolas de condiciones de carrera entre pedidos simultáneos.
"""

from negocio.interfaces.repositorios import UnitOfWork
from persistencia.database.connection import get_connection, transaction
from persistencia.repositories.sqlite_customer_repository import SqliteCustomerRepository
from persistencia.repositories.sqlite_order_item_repository import SqliteOrderItemRepository
from persistencia.repositories.sqlite_order_repository import SqliteOrderRepository
from persistencia.repositories.sqlite_product_repository import SqliteProductRepository


class SqliteUnitOfWork(UnitOfWork):
    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self._conn = None
        self._txn = None

    def __enter__(self) -> "SqliteUnitOfWork":
        self._conn = get_connection(self._db_path) if self._db_path else get_connection()
        self._txn = transaction(self._conn)
        self._txn.__enter__()
        self.customers = SqliteCustomerRepository(self._conn)
        self.products = SqliteProductRepository(self._conn)
        self.orders = SqliteOrderRepository(self._conn)
        self.order_items = SqliteOrderItemRepository(self._conn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            self._txn.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self._conn.close()
        return False
