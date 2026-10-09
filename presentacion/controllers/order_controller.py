"""
OrderController — adaptador HTTP para OrderService.

Capa de Presentación: recibe la solicitud HTTP ya parseada como dict,
delega la decisión completa (pedido pendiente, stock, descuentos,
DevPoints, transición de estado) en OrderService y traduce el
resultado u error a una respuesta JSON. No decide nada de negocio.
"""

from negocio.domain.enums import EstadoPedido, TipoPedido
from negocio.excepciones import ErrorNegocio, ValidacionError
from negocio.services.order_service import OrderService
from presentacion.controllers.errores_http import responder_error
from presentacion.controllers.serializers import pedido_a_dict


class OrderController:
    def __init__(self, order_service: OrderService):
        self._service = order_service

    def listar_todos(self):
        pedidos = self._service.listar_todos_los_pedidos()
        return 200, [pedido_a_dict(p) for p in pedidos]

    def listar_por_cliente(self, cliente_id: int):
        pedidos = self._service.listar_pedidos_de_cliente(cliente_id)
        return 200, [pedido_a_dict(p) for p in pedidos]

    def obtener(self, pedido_id: int):
        try:
            pedido = self._service.obtener_pedido(pedido_id)
            return 200, pedido_a_dict(pedido)
        except ErrorNegocio as e:
            return responder_error(e)

    def tiene_pendiente(self, cliente_id: int):
        existe = self._service.tiene_pedido_pendiente(cliente_id)
        return 200, {"tiene_pedido_pendiente": existe}

    def crear(self, body: dict):
        try:
            cliente_id = body.get("cliente_id")
            tipo_pedido_raw = body.get("tipo_pedido")
            numero_mesa = body.get("numero_mesa")
            puntos_a_redimir = body.get("puntos_a_redimir", 0)
            items = body.get("items")

            if cliente_id is None:
                raise ValidacionError("cliente_id es obligatorio.")
            if tipo_pedido_raw not in (TipoPedido.MESA.value, TipoPedido.LLEVAR.value):
                raise ValidacionError("tipo_pedido debe ser 'MESA' o 'LLEVAR'.")
            if not isinstance(items, list) or len(items) == 0:
                raise ValidacionError("items debe ser una lista no vacía.")

            items_normalizados = []
            for item in items:
                if "producto_id" not in item or "cantidad" not in item:
                    raise ValidacionError("Cada ítem requiere producto_id y cantidad.")
                items_normalizados.append(
                    {"producto_id": int(item["producto_id"]), "cantidad": int(item["cantidad"])}
                )

            pedido = self._service.crear_pedido(
                cliente_id=int(cliente_id),
                tipo_pedido=TipoPedido(tipo_pedido_raw),
                items_solicitados=items_normalizados,
                numero_mesa=int(numero_mesa) if numero_mesa else None,
                puntos_a_redimir=int(puntos_a_redimir or 0),
            )
            return 201, pedido_a_dict(pedido)
        except ErrorNegocio as e:
            return responder_error(e)
        except (TypeError, ValueError):
            return 400, {"error": "Datos de pedido inválidos.", "tipo": "ValidacionError"}

    def cambiar_estado(self, pedido_id: int, body: dict):
        try:
            nuevo_estado_raw = body.get("estado")
            try:
                nuevo_estado = EstadoPedido(nuevo_estado_raw)
            except ValueError:
                raise ValidacionError(f"Estado '{nuevo_estado_raw}' no es válido.")
            pedido = self._service.cambiar_estado(pedido_id, nuevo_estado)
            return 200, pedido_a_dict(pedido)
        except ErrorNegocio as e:
            return responder_error(e)
