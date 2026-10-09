"""
Traducción de excepciones de negocio a códigos de estado HTTP.

Es la única pieza de la capa de Presentación que "entiende" las
excepciones de negocio; se limita a elegir un código HTTP, nunca
decide si la operación es válida.
"""

from negocio.excepciones import (
    CantidadInvalidaError,
    ClienteNoEncontradoError,
    CorreoDuplicadoError,
    ErrorNegocio,
    PedidoNoEncontradoError,
    PedidoPendienteExistenteError,
    ProductoNoEncontradoError,
    RedencionInvalidaError,
    StockInsuficienteError,
    TransicionEstadoInvalidaError,
    ValidacionError,
)

_MAPA_CODIGOS = {
    ValidacionError: 400,
    CantidadInvalidaError: 400,
    RedencionInvalidaError: 400,
    ClienteNoEncontradoError: 404,
    ProductoNoEncontradoError: 404,
    PedidoNoEncontradoError: 404,
    PedidoPendienteExistenteError: 409,
    StockInsuficienteError: 409,
    TransicionEstadoInvalidaError: 409,
    CorreoDuplicadoError: 409,
}


def responder_error(exc: ErrorNegocio):
    codigo = _MAPA_CODIGOS.get(type(exc), 400)
    return codigo, {"error": str(exc), "tipo": type(exc).__name__}
