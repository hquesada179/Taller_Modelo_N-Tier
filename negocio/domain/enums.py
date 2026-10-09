"""Enumeraciones del dominio. Capa de Negocio — sin SQL, sin HTTP."""

from enum import Enum


class NivelLealtad(str, Enum):
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"


class EstadoPedido(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    IN_PREPARATION = "IN_PREPARATION"
    READY = "READY"
    DELIVERED = "DELIVERED"


class TipoPedido(str, Enum):
    MESA = "MESA"
    LLEVAR = "LLEVAR"


# Transiciones válidas de estado: no se permiten retrocesos arbitrarios.
TRANSICIONES_VALIDAS = {
    EstadoPedido.PENDING_PAYMENT: {EstadoPedido.IN_PREPARATION},
    EstadoPedido.IN_PREPARATION: {EstadoPedido.READY},
    EstadoPedido.READY: {EstadoPedido.DELIVERED},
    EstadoPedido.DELIVERED: set(),
}
