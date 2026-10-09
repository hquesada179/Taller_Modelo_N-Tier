"""CustomerController — adaptador HTTP para CustomerService."""

from negocio.excepciones import ErrorNegocio
from negocio.services.customer_service import CustomerService
from presentacion.controllers.errores_http import responder_error
from presentacion.controllers.serializers import cliente_a_dict


class CustomerController:
    def __init__(self, customer_service: CustomerService):
        self._service = customer_service

    def listar(self):
        clientes = self._service.listar_clientes()
        return 200, [cliente_a_dict(c) for c in clientes]

    def obtener(self, cliente_id: int):
        try:
            cliente = self._service.obtener_cliente(cliente_id)
            return 200, cliente_a_dict(cliente)
        except ErrorNegocio as e:
            return responder_error(e)

    def obtener_por_correo(self, correo: str):
        try:
            cliente = self._service.obtener_por_correo(correo)
            return 200, cliente_a_dict(cliente)
        except ErrorNegocio as e:
            return responder_error(e)

    def crear(self, body: dict):
        try:
            nombre = body.get("nombre")
            correo = body.get("correo")
            cliente = self._service.crear_cliente(nombre, correo)
            return 201, cliente_a_dict(cliente)
        except ErrorNegocio as e:
            return responder_error(e)
