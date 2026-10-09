"""
ProductController — adaptador HTTP para ProductService.

Recibe datos ya parseados (dict de JSON), hace únicamente validación
SINTÁCTICA de presencia/tipo de campos, delega toda regla de negocio
en ProductService y serializa la respuesta. No ejecuta SQL ni calcula
nada de negocio.
"""

from negocio.excepciones import ErrorNegocio
from negocio.services.product_service import ProductService
from presentacion.controllers.errores_http import responder_error
from presentacion.controllers.serializers import producto_a_dict


class ProductController:
    def __init__(self, product_service: ProductService):
        self._service = product_service

    def listar(self, query_params: dict):
        solo_activos = query_params.get("todos", ["0"])[0] != "1"
        productos = self._service.listar_productos(solo_activos=solo_activos)
        return 200, [producto_a_dict(p) for p in productos]

    def obtener(self, producto_id: int):
        try:
            producto = self._service.obtener_producto(producto_id)
            return 200, producto_a_dict(producto)
        except ErrorNegocio as e:
            return responder_error(e)

    def crear(self, body: dict):
        try:
            nombre = body.get("nombre")
            precio_base = body.get("precio_base")
            stock_inicial = body.get("stock_disponible", 0)
            producto = self._service.crear_producto(nombre, precio_base, stock_inicial)
            return 201, producto_a_dict(producto)
        except ErrorNegocio as e:
            return responder_error(e)

    def actualizar(self, producto_id: int, body: dict):
        try:
            nombre = body.get("nombre")
            precio_base = body.get("precio_base")
            activo = body.get("activo", True)
            producto = self._service.actualizar_producto(producto_id, nombre, precio_base, activo)
            return 200, producto_a_dict(producto)
        except ErrorNegocio as e:
            return responder_error(e)

    def ajustar_inventario(self, producto_id: int, body: dict):
        try:
            delta = body.get("delta")
            if delta is None:
                return 400, {"error": "El campo 'delta' es obligatorio.", "tipo": "ValidacionError"}
            producto = self._service.ajustar_inventario(producto_id, int(delta))
            return 200, producto_a_dict(producto)
        except ErrorNegocio as e:
            return responder_error(e)
