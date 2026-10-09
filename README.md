# Café Overflow — Dev & Coffee Lounge

Aplicación web de gestión de pedidos para una cafetería temática de desarrolladores de software, construida como **Taller de Arquitectura N-Tier** (asignatura Arquitectura de Software, UNAB).

## 1. Descripción del proyecto

Café Overflow es un sistema de pedidos para cafetería que permite:

- Consultar el menú de productos y su disponibilidad.
- Identificarse o registrarse como cliente.
- Armar un pedido (varios productos y cantidades), para mesa o para llevar.
- Ver el descuento aplicado por nivel de lealtad y por redención de DevPoints, **calculado siempre por el servidor**.
- Consultar el historial y estado de los propios pedidos.
- Administrar productos, inventario, clientes y el ciclo de vida de los pedidos desde un panel administrativo.

## 2. Objetivos del taller

- Implementar una arquitectura **N-Tier de tres capas lógicas** (Presentación, Negocio, Persistencia) con aislamiento real entre capas.
- Demostrar separación de responsabilidades (SoC): cada capa solo hace lo que le corresponde.
- Construir una aplicación funcional **sin frameworks**, usando únicamente la biblioteca estándar de Python y HTML/CSS/JS nativos.
- Implementar reglas de negocio no triviales (descuentos, fidelización, inventario, estados de pedido) de forma centralizada, consistente y con pruebas automatizadas.

## 3. Tecnologías utilizadas

| Capa | Tecnología |
|---|---|
| Presentación (frontend) | HTML5, CSS3, JavaScript nativo (sin frameworks) |
| Presentación (backend/HTTP) | Python 3, `http.server` (biblioteca estándar) |
| Negocio | Python 3 puro (sin dependencias externas) |
| Persistencia | SQLite vía `sqlite3` (biblioteca estándar, sin ORM) |
| Pruebas | `unittest` (biblioteca estándar) |

No se utiliza ningún framework (Flask, Django, FastAPI, Express, React, Vue, Angular, Spring Boot, etc.) ni ORM. El único paquete usado en todo el proyecto es la biblioteca estándar de Python.

## 4. Arquitectura de tres capas

```
          Navegador (HTML / CSS / JS nativo)
                      │  HTTP + JSON
                      ▼
   ┌───────────────────────────────────────────┐
   │   CAPA DE PRESENTACIÓN  (presentacion/)    │
   │   server.py + controllers/                 │
   │   - Enruta solicitudes HTTP                │
   │   - Parsea/serializa JSON                  │
   │   - Validación SINTÁCTICA                  │
   └───────────────────┬─────────────────────────┘
                      │  llamadas a servicios (objetos Python)
                      ▼
   ┌───────────────────────────────────────────┐
   │   CAPA DE NEGOCIO  (negocio/)               │
   │   services/ + domain/ + interfaces/         │
   │   - Reglas de negocio                       │
   │   - Descuentos, DevPoints, ascensos         │
   │   - Validación de stock y estados           │
   │   - NO conoce HTTP, JSON ni SQL             │
   └───────────────────┬─────────────────────────┘
                      │  interfaces de repositorio (ABC)
                      ▼
   ┌───────────────────────────────────────────┐
   │   CAPA DE PERSISTENCIA  (persistencia/)     │
   │   repositories/ + database/                 │
   │   - Ejecuta SQL                             │
   │   - Mapea filas ↔ entidades de dominio      │
   │   - Transacciones (Unit of Work)            │
   └───────────────────┬─────────────────────────┘
                      ▼
                   SQLite (archivo .db)
```

### 4.1. Capa de Presentación (`presentacion/`)

- `server.py` (raíz del proyecto): servidor HTTP (`http.server.ThreadingHTTPServer`), enrutamiento por expresiones regulares, serialización/deserialización JSON.
- `controllers/`: adaptadores HTTP → Negocio. Reciben un `dict` ya parseado, hacen validación sintáctica mínima (campos presentes, tipos), llaman al servicio correspondiente y traducen el resultado (o la excepción de negocio) a una respuesta HTTP + JSON. **No contienen ninguna regla de negocio.**
- `static/` (css, js, img) y `templates/` (`index.html` vista cliente, `admin.html` vista administrativa): HTML/CSS/JS servidos como archivos estáticos.

Prohibido explícitamente aquí (y verificado con una prueba automatizada): calcular descuentos, decidir ascensos de nivel, calcular DevPoints, ejecutar SQL o decidir si un pedido puede registrarse.

### 4.2. Capa de Negocio (`negocio/`)

- `domain/`: entidades (`Producto`, `Cliente`, `Pedido`, `ElementoPedido`) y enumeraciones (`NivelLealtad`, `EstadoPedido`, `TipoPedido`) como `dataclasses` puras de Python.
- `services/`: `DiscountService`, `StockService`, `ProductService`, `CustomerService`, `LoyaltyService`, `OrderService`. Contienen toda la lógica de negocio del taller (sección 6).
- `interfaces/repositorios.py`: contratos abstractos (`ABC`) de repositorio y de unidad de trabajo (`UnitOfWork`). La capa de Negocio depende únicamente de estas abstracciones, nunca de SQLite directamente.
- `excepciones.py`: excepciones de negocio (p. ej. `StockInsuficienteError`, `PedidoPendienteExistenteError`, `RedencionInvalidaError`).

Esta capa no importa `sqlite3`, `http`/`http.server` ni usa `json` como formato de transporte, y no contiene sentencias SQL literales — esto se verifica automáticamente en `tests/test_aislamiento_capas.py`.

### 4.3. Capa de Persistencia (`persistencia/`)

- `database/schema.sql`: definición DDL completa (tablas, claves foráneas, `CHECK`, índices).
- `database/connection.py`: apertura de conexiones SQLite configuradas (`PRAGMA foreign_keys`, `WAL`) y un *context manager* `transaction` que agrupa operaciones en una transacción atómica (`BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK`) protegida con un lock de proceso.
- `repositories/`: `SqliteCustomerRepository`, `SqliteProductRepository`, `SqliteOrderRepository`, `SqliteOrderItemRepository` — implementan las interfaces de `negocio/interfaces/` ejecutando SQL puro (sin ORM) y mapeando filas a entidades de dominio.
- `repositories/sqlite_unit_of_work.py`: `SqliteUnitOfWork`, que abre una conexión + transacción por operación de negocio y expone los cuatro repositorios ya ligados a esa misma conexión/transacción.
- `init_db.py`: inicialización idempotente del esquema y datos de demostración.

Esta capa únicamente ejecuta SQL y mapea datos: no decide descuentos, niveles de lealtad ni condiciones de negocio.

## 5. Instalación y ejecución (Windows)

### Requisitos

- Python 3.10 o superior (verificado con Python 3.14) — sin paquetes adicionales, todo es biblioteca estándar.

### Pasos

```powershell
# 1. Ubicarse en la carpeta del proyecto
cd "Taller Modelo N-Tier"

# 2. (Opcional) Inicializar la base de datos explícitamente con datos de demostración
python -m persistencia.init_db

# 3. Iniciar el servidor (también inicializa la BD automáticamente si no existe)
python server.py
#   -> Vista cliente:        http://localhost:8000/
#   -> Vista administrativa: http://localhost:8000/admin
# Para usar otro puerto: python server.py 9000
```

La base de datos se guarda en `persistencia/database/cafe_overflow.db` y **persiste entre reinicios** del servidor (no se usa memoria ni `localStorage` como fuente de datos).

### Ejecución de las pruebas automatizadas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas de integración crean su propia base de datos SQLite temporal (independiente de `cafe_overflow.db`) en cada ejecución, por lo que no interfieren con los datos de demostración.

## 6. Reglas de negocio implementadas

Todas centralizadas en `negocio/services/`:

1. **Descuento por nivel** (`DiscountService`): Junior 5%, Mid 10%, Senior 15%, aplicado sobre el subtotal (porcentajes centralizados en `DiscountService.PORCENTAJES`).
2. **Ascenso automático** (`LoyaltyService.evaluar_nivel`): Junior → Mid al acumular $500.000 pagados; Mid → Senior al acumular $1.500.000 pagados. El nivel nunca retrocede, y el nuevo nivel solo aplica a compras *posteriores* (el descuento de la compra que provoca el ascenso ya fue calculado con el nivel anterior).
3. **DevPoints** (`LoyaltyService`): 1 DevPoint por cada $20.000 efectivamente pagados en un pedido `DELIVERED`; cada DevPoint redime $200. Política explícita: tanto los DevPoints otorgados como el monto que cuenta para el ascenso se calculan sobre `total_calculado` (el monto pagado *después* de descuentos), no sobre el subtotal bruto.
4. **Validación de stock** (`StockService`): rechaza cantidades ≤ 0, productos inexistentes/inactivos y cantidades mayores al stock disponible; el stock se descuenta **inmediatamente** al crear el pedido, dentro de la misma transacción que crea el pedido y sus ítems (ver política de reserva más abajo).
5. **Un pedido pendiente por cliente** (`OrderRepository.existe_pendiente_de_pago` + `OrderService`): un cliente con un pedido en `PENDING_PAYMENT` no puede crear otro.
6. **Estados del pedido**: `PENDING_PAYMENT → IN_PREPARATION → READY → DELIVERED`, sin retrocesos ni saltos (tabla `TRANSICIONES_VALIDAS` en `negocio/domain/enums.py`). `DELIVERED` es el evento de finalización: ahí se aplican los beneficios de fidelización **exactamente una vez** (bandera `beneficios_aplicados`).

### Políticas de implementación documentadas explícitamente

- **Momento del descuento de inventario**: el stock se descuenta de inmediato al crear el pedido (no hay un paso separado de "reserva" seguido de confirmación). Este descuento inmediato actúa como la reserva y evita sobreventa en pedidos concurrentes, ya que ocurre dentro de la misma transacción SQLite (`BEGIN IMMEDIATE`) serializada por un lock de proceso.
- **Momento de redención de DevPoints**: los puntos redimidos se descuentan del saldo del cliente **al crear el pedido** (misma lógica de reserva inmediata que el stock), para evitar que el mismo saldo se redima dos veces en pedidos concurrentes del mismo cliente.
- **Momento de otorgamiento de DevPoints y acumulado de compras**: ocurre únicamente cuando el pedido pasa a `DELIVERED`, y exactamente una vez por pedido.
- **Base de cálculo**: tanto los DevPoints otorgados como el monto acumulado para el ascenso de nivel usan el monto *efectivamente pagado* (`total_calculado`), según se definió como convención del proyecto.

## 7. Funcionalidades

**Vista cliente** (`/`): identificación/registro por correo, menú con stock visible, carrito, selección de tipo de pedido (mesa/para llevar), redención de DevPoints, confirmación con desglose de descuentos calculado por el servidor, consulta de nivel/DevPoints/acumulado, historial y estado de pedidos propios.

**Vista administrativa** (`/admin`): alta/edición de productos, ajuste manual de inventario, listado y alta de clientes (con nivel, DevPoints y acumulado visibles), listado de todos los pedidos con avance guiado de estado.

## 8. Estructura del proyecto

```
Taller Modelo N-Tier/
├── server.py                  # Punto de entrada HTTP (Presentación)
├── presentacion/
│   ├── controllers/           # Adaptadores HTTP -> Negocio
│   ├── static/{css,js,img}/   # HTML estático / CSS / JS nativo
│   └── templates/             # index.html (cliente), admin.html
├── negocio/
│   ├── domain/                # Entidades y enums del dominio
│   ├── services/               # Reglas de negocio
│   ├── interfaces/             # Contratos de repositorio (ABC)
│   └── excepciones.py
├── persistencia/
│   ├── database/               # schema.sql, connection.py
│   ├── repositories/           # Implementaciones SQLite
│   └── init_db.py
├── tests/                      # unittest (negocio + integración + arquitectura)
├── diagrams/                   # Diagramas C4 (Nivel1.png, nivel2.png, Nivel3.png)
├── .gitignore
└── README.md
```

## 9. Diagramas C4

Los diagramas C4 de Contexto (nivel 1), Contenedores (nivel 2) y Componentes (nivel 3), elaborados previamente para este taller, se encuentran en `diagrams/`:

- `diagrams/Nivel1.png`
- `diagrams/nivel2.png`
- `diagrams/Nivel3.png`

La implementación final (carpetas `presentacion/`, `negocio/`, `persistencia/`, componentes `OrderController`, `DiscountService`, `StockService`, `ProductService`, `CustomerService`, `LoyaltyService`, `OrderService`, `*Repository`) corresponde a los componentes identificados en el diagrama de Nivel 3.

## 10. Limitaciones conocidas

- No existe un estado de "cancelado" ni flujo de reembolso: si un pedido queda en `PENDING_PAYMENT` o `IN_PREPARATION` indefinidamente, el stock y los DevPoints ya descontados **no se reintegran automáticamente** en esta versión (no estaba dentro del alcance solicitado por el taller, que exige únicamente los cuatro estados indicados).
- No se implementan pagos reales ni integraciones bancarias (explícitamente fuera de alcance).
- La concurrencia entre escrituras se serializa mediante un lock de proceso + transacciones SQLite `BEGIN IMMEDIATE`; esto es correcto y se prueba automáticamente (`tests/test_order_service_integration.py`), pero al ejecutarse en un único proceso Python no se validó bajo múltiples procesos/instancias del servidor.
- La autenticación de clientes es por correo electrónico sin contraseña (identificación simple), acorde al alcance académico del taller; no se implementó gestión de sesiones ni seguridad de credenciales.
- El servidor HTTP (`http.server`) es apto para fines académicos y de demostración; no está pensado para producción de alto tráfico.
