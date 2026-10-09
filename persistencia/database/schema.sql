-- ============================================================
-- Café Overflow — Dev & Coffee Lounge
-- Esquema de base de datos SQLite (capa de Persistencia)
-- ============================================================
-- Todos los montos monetarios se almacenan como ENTEROS (pesos
-- colombianos, COP) para evitar errores de coma flotante.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Tabla: customers
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                      TEXT    NOT NULL,
    correo                      TEXT    NOT NULL UNIQUE,
    nivel_lealtad               TEXT    NOT NULL DEFAULT 'JUNIOR'
                                        CHECK (nivel_lealtad IN ('JUNIOR', 'MID', 'SENIOR')),
    saldo_devpoints             INTEGER NOT NULL DEFAULT 0
                                        CHECK (saldo_devpoints >= 0),
    monto_acumulado_compras     INTEGER NOT NULL DEFAULT 0
                                        CHECK (monto_acumulado_compras >= 0),
    fecha_creacion              TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Tabla: products
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT    NOT NULL,
    precio_base         INTEGER NOT NULL CHECK (precio_base >= 0),
    stock_disponible    INTEGER NOT NULL DEFAULT 0 CHECK (stock_disponible >= 0),
    activo              INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

-- ------------------------------------------------------------
-- Tabla: orders (Pedido)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id              INTEGER NOT NULL,
    fecha                   TEXT    NOT NULL DEFAULT (datetime('now')),
    estado                  TEXT    NOT NULL DEFAULT 'PENDING_PAYMENT'
                                    CHECK (estado IN ('PENDING_PAYMENT', 'IN_PREPARATION', 'READY', 'DELIVERED')),
    subtotal                INTEGER NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    descuento_nivel         INTEGER NOT NULL DEFAULT 0 CHECK (descuento_nivel >= 0),
    descuento_devpoints     INTEGER NOT NULL DEFAULT 0 CHECK (descuento_devpoints >= 0),
    total_calculado         INTEGER NOT NULL DEFAULT 0 CHECK (total_calculado >= 0),
    devpoints_redimidos     INTEGER NOT NULL DEFAULT 0 CHECK (devpoints_redimidos >= 0),
    devpoints_otorgados     INTEGER NOT NULL DEFAULT 0 CHECK (devpoints_otorgados >= 0),
    beneficios_aplicados    INTEGER NOT NULL DEFAULT 0 CHECK (beneficios_aplicados IN (0, 1)),
    tipo_pedido             TEXT    NOT NULL CHECK (tipo_pedido IN ('MESA', 'LLEVAR')),
    numero_mesa             INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES customers (id) ON DELETE RESTRICT,
    CHECK (
        (tipo_pedido = 'MESA' AND numero_mesa IS NOT NULL AND numero_mesa > 0)
        OR (tipo_pedido = 'LLEVAR' AND numero_mesa IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_orders_cliente ON orders (cliente_id);
CREATE INDEX IF NOT EXISTS idx_orders_estado ON orders (estado);

-- ------------------------------------------------------------
-- Tabla: order_items (ElementoPedido)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id           INTEGER NOT NULL,
    producto_id         INTEGER NOT NULL,
    cantidad            INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario     INTEGER NOT NULL CHECK (precio_unitario >= 0),
    subtotal            INTEGER NOT NULL CHECK (subtotal >= 0),
    FOREIGN KEY (pedido_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_order_items_pedido ON order_items (pedido_id);
CREATE INDEX IF NOT EXISTS idx_order_items_producto ON order_items (producto_id);
