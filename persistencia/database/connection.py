"""
Gestión de la conexión a SQLite (capa de Persistencia).

Responsabilidad única: abrir conexiones configuradas correctamente
(foreign_keys, row_factory, modo de journal) y ofrecer un helper de
transacción. No contiene ninguna regla de negocio.
"""

import os
import sqlite3
import threading

_DB_FILENAME = "cafe_overflow.db"
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(_BASE_DIR, _DB_FILENAME)
SCHEMA_PATH = os.path.join(_BASE_DIR, "schema.sql")

_lock = threading.Lock()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Crea una conexión nueva, correctamente configurada."""
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: str = SCHEMA_PATH) -> None:
    """Ejecuta el script DDL del esquema (idempotente, usa IF NOT EXISTS)."""
    with open(schema_path, "r", encoding="utf-8") as f:
        script = f.read()
    conn.executescript(script)


class transaction:
    """
    Context manager que agrupa varias operaciones de escritura en una
    única transacción SQLite, serializada con un lock de proceso para
    evitar condiciones de carrera entre hilos del servidor HTTP al
    descontar stock o registrar pedidos simultáneos.

    Uso:
        with transaction(conn):
            conn.execute(...)
            conn.execute(...)
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        _lock.acquire()
        self._conn.execute("BEGIN IMMEDIATE;")
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            if exc_type is None:
                self._conn.execute("COMMIT;")
            else:
                self._conn.execute("ROLLBACK;")
        finally:
            _lock.release()
        return False
