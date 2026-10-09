"""
Script de inicialización de la base de datos.

Crea el esquema si no existe y, si la tabla de productos está vacía,
inserta datos de demostración (productos de catálogo). Es idempotente:
puede ejecutarse varias veces sin duplicar datos ni borrar pedidos o
clientes ya existentes.

Uso:
    python -m persistencia.init_db
"""

from persistencia.database.connection import DEFAULT_DB_PATH, get_connection, init_schema

PRODUCTOS_DEMO = [
    ("Espresso StackTrace", 6000, 50),
    ("Latte NullPointer", 8500, 40),
    ("Cappuccino RecursionError", 9000, 35),
    ("Americano SegFault", 6500, 45),
    ("Combo BugHunter", 18000, 25),
    ("Té Async/Await", 7000, 30),
    ("Mocha DeadLock", 9500, 20),
    ("Croissant HelloWorld", 5500, 30),
    ("Galleta Byte-Size", 3500, 60),
    ("Frappé Kernel Panic", 11000, 15),
]


def poblar_datos_demo(conn) -> None:
    (total,) = conn.execute("SELECT COUNT(*) FROM products;").fetchone()
    if total > 0:
        return
    conn.execute("BEGIN IMMEDIATE;")
    try:
        for nombre, precio, stock in PRODUCTOS_DEMO:
            conn.execute(
                "INSERT INTO products (nombre, precio_base, stock_disponible, activo) "
                "VALUES (?, ?, ?, 1);",
                (nombre, precio, stock),
            )
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def main(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        init_schema(conn)
        poblar_datos_demo(conn)
        print(f"Base de datos inicializada en: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
