"""Excepciones de la capa de Negocio. Representan violaciones de reglas
de negocio, nunca errores de SQL ni de HTTP."""


class ErrorNegocio(Exception):
    """Excepción base de todas las reglas de negocio."""


class ClienteNoEncontradoError(ErrorNegocio):
    pass


class ProductoNoEncontradoError(ErrorNegocio):
    pass


class PedidoNoEncontradoError(ErrorNegocio):
    pass


class PedidoPendienteExistenteError(ErrorNegocio):
    """El cliente ya tiene un pedido PENDING_PAYMENT."""


class StockInsuficienteError(ErrorNegocio):
    pass


class CantidadInvalidaError(ErrorNegocio):
    pass


class RedencionInvalidaError(ErrorNegocio):
    pass


class TransicionEstadoInvalidaError(ErrorNegocio):
    pass


class ValidacionError(ErrorNegocio):
    pass


class CorreoDuplicadoError(ErrorNegocio):
    pass
