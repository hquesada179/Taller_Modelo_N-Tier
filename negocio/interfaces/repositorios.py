"""
Interfaces (contratos) de repositorio.

La capa de Negocio depende únicamente de estas abstracciones, nunca de
una implementación concreta de SQLite. Esto permite, por ejemplo,
sustituir la persistencia en pruebas sin tocar los servicios.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from negocio.domain.entidades import Cliente, ElementoPedido, Pedido, Producto
from negocio.domain.enums import EstadoPedido


class CustomerRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    def listar_todos(self) -> List[Cliente]:
        ...

    @abstractmethod
    def crear(self, cliente: Cliente) -> Cliente:
        ...

    @abstractmethod
    def actualizar(self, cliente: Cliente) -> None:
        ...


class ProductRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        ...

    @abstractmethod
    def listar_todos(self, solo_activos: bool = True) -> List[Producto]:
        ...

    @abstractmethod
    def crear(self, producto: Producto) -> Producto:
        ...

    @abstractmethod
    def actualizar(self, producto: Producto) -> None:
        ...

    @abstractmethod
    def ajustar_stock(self, producto_id: int, delta: int) -> None:
        """Aplica un delta (positivo o negativo) al stock disponible."""
        ...


class OrderRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, pedido_id: int) -> Optional[Pedido]:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: int) -> List[Pedido]:
        ...

    @abstractmethod
    def listar_todos(self) -> List[Pedido]:
        ...

    @abstractmethod
    def existe_pendiente_de_pago(self, cliente_id: int) -> bool:
        ...

    @abstractmethod
    def crear(self, pedido: Pedido) -> Pedido:
        ...

    @abstractmethod
    def actualizar_estado(self, pedido_id: int, nuevo_estado: EstadoPedido) -> None:
        ...

    @abstractmethod
    def actualizar_totales_y_beneficios(self, pedido: Pedido) -> None:
        ...


class OrderItemRepository(ABC):
    @abstractmethod
    def listar_por_pedido(self, pedido_id: int) -> List[ElementoPedido]:
        ...

    @abstractmethod
    def crear(self, elemento: ElementoPedido) -> ElementoPedido:
        ...


class UnitOfWork(ABC):
    """
    Abstracción de una unidad de trabajo transaccional. Permite a los
    servicios de negocio coordinar varias operaciones de repositorio
    como una sola transacción atómica, sin conocer SQLite.
    """

    customers: CustomerRepository
    products: ProductRepository
    orders: OrderRepository
    order_items: OrderItemRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        ...
