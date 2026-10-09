"""
Café Overflow — Dev & Coffee Lounge
Punto de entrada del servidor HTTP (capa de Presentación).

Implementado únicamente con la biblioteca estándar de Python
(http.server). Responsabilidades de este archivo:
  - Servir los archivos estáticos (HTML/CSS/JS) de la aplicación.
  - Enrutar solicitudes /api/** hacia los controladores HTTP.
  - Convertir el cuerpo de la solicitud (JSON) en diccionarios y las
    respuestas de los controladores en JSON.

NO contiene reglas de negocio: todo lo delega a los controladores,
que a su vez delegan en los servicios de la capa de Negocio.

Ejecución:
    python server.py [puerto]
"""

import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from negocio.services.customer_service import CustomerService
from negocio.services.order_service import OrderService
from negocio.services.product_service import ProductService
from persistencia.database.connection import DEFAULT_DB_PATH, get_connection, init_schema
from persistencia.init_db import poblar_datos_demo
from persistencia.repositories.sqlite_unit_of_work import SqliteUnitOfWork
from presentacion.controllers.customer_controller import CustomerController
from presentacion.controllers.order_controller import OrderController
from presentacion.controllers.product_controller import ProductController

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "presentacion", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "presentacion", "templates")


def _uow_factory():
    return SqliteUnitOfWork(DEFAULT_DB_PATH)


product_service = ProductService(_uow_factory)
customer_service = CustomerService(_uow_factory)
order_service = OrderService(_uow_factory)

product_controller = ProductController(product_service)
customer_controller = CustomerController(customer_service)
order_controller = OrderController(order_service)


# ------------------------------------------------------------
# Tabla de rutas: (método, patrón regex, manejador)
# El manejador recibe (handler, match, query, body) y retorna (status, payload)
# ------------------------------------------------------------
def _ruta_productos_listar(h, m, q, b):
    return product_controller.listar(q)


def _ruta_productos_obtener(h, m, q, b):
    return product_controller.obtener(int(m.group(1)))


def _ruta_productos_crear(h, m, q, b):
    return product_controller.crear(b)


def _ruta_productos_actualizar(h, m, q, b):
    return product_controller.actualizar(int(m.group(1)), b)


def _ruta_productos_inventario(h, m, q, b):
    return product_controller.ajustar_inventario(int(m.group(1)), b)


def _ruta_clientes_listar(h, m, q, b):
    return customer_controller.listar()


def _ruta_clientes_crear(h, m, q, b):
    return customer_controller.crear(b)


def _ruta_clientes_obtener(h, m, q, b):
    return customer_controller.obtener(int(m.group(1)))


def _ruta_clientes_por_correo(h, m, q, b):
    return customer_controller.obtener_por_correo(unquote(m.group(1)))


def _ruta_clientes_pedidos(h, m, q, b):
    return order_controller.listar_por_cliente(int(m.group(1)))


def _ruta_clientes_pedido_pendiente(h, m, q, b):
    return order_controller.tiene_pendiente(int(m.group(1)))


def _ruta_pedidos_listar(h, m, q, b):
    return order_controller.listar_todos()


def _ruta_pedidos_crear(h, m, q, b):
    return order_controller.crear(b)


def _ruta_pedidos_obtener(h, m, q, b):
    return order_controller.obtener(int(m.group(1)))


def _ruta_pedidos_estado(h, m, q, b):
    return order_controller.cambiar_estado(int(m.group(1)), b)


ROUTES = [
    ("GET", re.compile(r"^/api/productos$"), _ruta_productos_listar),
    ("GET", re.compile(r"^/api/productos/(\d+)$"), _ruta_productos_obtener),
    ("POST", re.compile(r"^/api/productos$"), _ruta_productos_crear),
    ("PUT", re.compile(r"^/api/productos/(\d+)$"), _ruta_productos_actualizar),
    ("POST", re.compile(r"^/api/productos/(\d+)/inventario$"), _ruta_productos_inventario),
    ("GET", re.compile(r"^/api/clientes$"), _ruta_clientes_listar),
    ("POST", re.compile(r"^/api/clientes$"), _ruta_clientes_crear),
    ("GET", re.compile(r"^/api/clientes/correo/([^/]+)$"), _ruta_clientes_por_correo),
    ("GET", re.compile(r"^/api/clientes/(\d+)$"), _ruta_clientes_obtener),
    ("GET", re.compile(r"^/api/clientes/(\d+)/pedidos$"), _ruta_clientes_pedidos),
    ("GET", re.compile(r"^/api/clientes/(\d+)/pedido-pendiente$"), _ruta_clientes_pedido_pendiente),
    ("GET", re.compile(r"^/api/pedidos$"), _ruta_pedidos_listar),
    ("POST", re.compile(r"^/api/pedidos$"), _ruta_pedidos_crear),
    ("GET", re.compile(r"^/api/pedidos/(\d+)$"), _ruta_pedidos_obtener),
    ("PATCH", re.compile(r"^/api/pedidos/(\d+)/estado$"), _ruta_pedidos_estado),
]

PAGINAS = {
    "/": os.path.join(TEMPLATES_DIR, "index.html"),
    "/index.html": os.path.join(TEMPLATES_DIR, "index.html"),
    "/admin": os.path.join(TEMPLATES_DIR, "admin.html"),
    "/admin.html": os.path.join(TEMPLATES_DIR, "admin.html"),
}


class CafeOverflowHandler(BaseHTTPRequestHandler):
    server_version = "CafeOverflow/1.0"

    def log_message(self, format, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    # ---------------- utilitarios de respuesta ----------------
    def _enviar_json(self, status: int, payload):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _enviar_archivo(self, ruta_absoluta: str):
        if not os.path.isfile(ruta_absoluta):
            self._enviar_json(404, {"error": "Recurso no encontrado."})
            return
        tipo, _ = mimetypes.guess_type(ruta_absoluta)
        with open(ruta_absoluta, "rb") as f:
            contenido = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo or "application/octet-stream")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def _leer_cuerpo_json(self) -> dict:
        largo = int(self.headers.get("Content-Length", 0))
        if largo == 0:
            return {}
        crudo = self.rfile.read(largo)
        try:
            return json.loads(crudo.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _servir_estatico(self, ruta_pedida: str) -> bool:
        """Sirve archivos bajo /static/, evitando salir del directorio."""
        if not ruta_pedida.startswith("/static/"):
            return False
        relativo = unquote(ruta_pedida[len("/static/"):])
        destino = os.path.abspath(os.path.join(STATIC_DIR, relativo))
        if not destino.startswith(os.path.abspath(STATIC_DIR)):
            self._enviar_json(403, {"error": "Acceso denegado."})
            return True
        self._enviar_archivo(destino)
        return True

    def _despachar(self, metodo: str):
        parsed = urlparse(self.path)
        ruta = parsed.path
        query = parse_qs(parsed.query)

        if metodo == "GET" and (ruta in PAGINAS or self._servir_estatico(ruta)):
            if ruta in PAGINAS:
                self._enviar_archivo(PAGINAS[ruta])
            return

        for metodo_ruta, patron, manejador in ROUTES:
            if metodo_ruta != metodo:
                continue
            coincidencia = patron.match(ruta)
            if coincidencia:
                cuerpo = self._leer_cuerpo_json() if metodo in ("POST", "PUT", "PATCH") else {}
                try:
                    status, payload = manejador(self, coincidencia, query, cuerpo)
                except Exception as exc:  # salvaguarda: nunca exponer trazas internas
                    self.log_message("Error interno: %s", exc)
                    status, payload = 500, {"error": "Error interno del servidor."}
                self._enviar_json(status, payload)
                return

        self._enviar_json(404, {"error": f"Ruta no encontrada: {metodo} {ruta}"})

    def do_GET(self):
        self._despachar("GET")

    def do_POST(self):
        self._despachar("POST")

    def do_PUT(self):
        self._despachar("PUT")

    def do_PATCH(self):
        self._despachar("PATCH")


def preparar_base_de_datos():
    conn = get_connection(DEFAULT_DB_PATH)
    try:
        init_schema(conn)
        poblar_datos_demo(conn)
    finally:
        conn.close()


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    preparar_base_de_datos()
    servidor = ThreadingHTTPServer(("0.0.0.0", puerto), CafeOverflowHandler)
    print(f"Café Overflow escuchando en http://localhost:{puerto}")
    print(f"  - Vista cliente:        http://localhost:{puerto}/")
    print(f"  - Vista administrativa: http://localhost:{puerto}/admin")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        servidor.shutdown()


if __name__ == "__main__":
    main()
