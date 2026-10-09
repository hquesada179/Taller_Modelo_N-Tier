"""
StockService — capa de Negocio.

Valida disponibilidad de inventario y coordina su reducción. Nunca
ejecuta SQL directamente: delega en ProductRepository (a través de la
unidad de trabajo) para leer y modificar el stock.

Política de reserva de inventario: el stock se descuenta de forma
INMEDIATA al crear el pedido (dentro de la misma transacción que
registra el pedido y sus ítems). No existe un paso separado de
"reserva temporal" seguido de confirmación; el descuento inmediato
actúa como la reserva, evitando sobreventa cuando llegan pedidos
concurrentes para el mismo producto.
"""

from negocio.domain.entidades import Producto
from negocio.excepciones import CantidadInvalidaError, StockInsuficienteError
from negocio.interfaces.repositorios import ProductRepository


class StockService:
    @staticmethod
    def validar_cantidad_positiva(cantidad: int) -> None:
        if cantidad is None or cantidad <= 0:
            raise CantidadInvalidaError("La cantidad debe ser un entero positivo.")

    @staticmethod
    def validar_disponibilidad(producto: Producto, cantidad: int) -> None:
        StockService.validar_cantidad_positiva(cantidad)
        if cantidad > producto.stock_disponible:
            raise StockInsuficienteError(
                f"Stock insuficiente para '{producto.nombre}': "
                f"solicitado {cantidad}, disponible {producto.stock_disponible}."
            )

    @staticmethod
    def descontar_stock(repo: ProductRepository, producto_id: int, cantidad: int) -> None:
        """
        Descuenta `cantidad` unidades del producto. Debe invocarse
        siempre después de `validar_disponibilidad` dentro de la misma
        transacción, para que la verificación y el descuento sean
        atómicos frente a pedidos simultáneos.
        """
        StockService.validar_cantidad_positiva(cantidad)
        repo.ajustar_stock(producto_id, -cantidad)
