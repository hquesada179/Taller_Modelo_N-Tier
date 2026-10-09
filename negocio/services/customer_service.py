"""CustomerService — capa de Negocio. Gestión de clientes."""

import re
from typing import Callable, List

from negocio.domain.entidades import Cliente
from negocio.domain.enums import NivelLealtad
from negocio.excepciones import ClienteNoEncontradoError, CorreoDuplicadoError, ValidacionError
from negocio.interfaces.repositorios import UnitOfWork

_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CustomerService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def listar_clientes(self) -> List[Cliente]:
        with self._uow_factory() as uow:
            return uow.customers.listar_todos()

    def obtener_cliente(self, cliente_id: int) -> Cliente:
        with self._uow_factory() as uow:
            cliente = uow.customers.obtener_por_id(cliente_id)
            if cliente is None:
                raise ClienteNoEncontradoError(f"Cliente {cliente_id} no existe.")
            return cliente

    def obtener_por_correo(self, correo: str) -> Cliente:
        with self._uow_factory() as uow:
            cliente = uow.customers.obtener_por_correo(correo)
            if cliente is None:
                raise ClienteNoEncontradoError(f"No existe cliente con correo {correo}.")
            return cliente

    def crear_cliente(self, nombre: str, correo: str) -> Cliente:
        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre es obligatorio.")
        if not correo or not _PATRON_CORREO.match(correo.strip()):
            raise ValidacionError("El correo electrónico no es válido.")
        correo_normalizado = correo.strip().lower()
        with self._uow_factory() as uow:
            if uow.customers.obtener_por_correo(correo_normalizado) is not None:
                raise CorreoDuplicadoError(f"Ya existe un cliente con el correo {correo_normalizado}.")
            # Todo cliente nuevo inicia en Junior, sin compras ni DevPoints.
            cliente = Cliente(
                id=None,
                nombre=nombre.strip(),
                correo=correo_normalizado,
                nivel_lealtad=NivelLealtad.JUNIOR,
                saldo_devpoints=0,
                monto_acumulado_compras=0,
            )
            return uow.customers.crear(cliente)
