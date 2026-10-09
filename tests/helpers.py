"""
Utilidades comunes para las pruebas de integración.

Cada prueba de integración trabaja sobre un archivo SQLite temporal e
independiente (no sobre la base de datos de demostración), inicializado
con el mismo esquema real de producción. Esto permite probar la pila
completa (Negocio + Persistencia) sin mocks de la base de datos.
"""

import os
import shutil
import tempfile
import unittest

from negocio.services.customer_service import CustomerService
from negocio.services.order_service import OrderService
from negocio.services.product_service import ProductService
from persistencia.database.connection import get_connection, init_schema
from persistencia.repositories.sqlite_unit_of_work import SqliteUnitOfWork


class BaseIntegrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp(prefix="cafe_overflow_test_")
        self.db_path = os.path.join(self._tmp_dir, "test.db")
        conn = get_connection(self.db_path)
        try:
            init_schema(conn)
        finally:
            conn.close()

        self.uow_factory = lambda: SqliteUnitOfWork(self.db_path)
        self.productos = ProductService(self.uow_factory)
        self.clientes = CustomerService(self.uow_factory)
        self.pedidos = OrderService(self.uow_factory)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def crear_cliente(self, nombre="Ada Lovelace", correo=None):
        correo = correo or f"{nombre.split()[0].lower()}@test.devcoffee"
        return self.clientes.crear_cliente(nombre, correo)

    def crear_producto(self, nombre="Espresso StackTrace", precio=6000, stock=10):
        return self.productos.crear_producto(nombre, precio, stock)
