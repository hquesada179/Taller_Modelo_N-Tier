"""ProductService — capa de Negocio. Gestión de productos e inventario."""

from typing import Callable, List

from negocio.domain.entidades import Producto
from negocio.excepciones import ProductoNoEncontradoError, ValidacionError
from negocio.interfaces.repositorios import UnitOfWork


class ProductService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def listar_productos(self, solo_activos: bool = True) -> List[Producto]:
        with self._uow_factory() as uow:
            return uow.products.listar_todos(solo_activos)

    def obtener_producto(self, producto_id: int) -> Producto:
        with self._uow_factory() as uow:
            producto = uow.products.obtener_por_id(producto_id)
            if producto is None:
                raise ProductoNoEncontradoError(f"Producto {producto_id} no existe.")
            return producto

    def crear_producto(self, nombre: str, precio_base: int, stock_inicial: int) -> Producto:
        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del producto es obligatorio.")
        if precio_base is None or precio_base < 0:
            raise ValidacionError("El precio base no puede ser negativo.")
        if stock_inicial is None or stock_inicial < 0:
            raise ValidacionError("El stock inicial no puede ser negativo.")
        with self._uow_factory() as uow:
            return uow.products.crear(
                Producto(id=None, nombre=nombre.strip(), precio_base=precio_base, stock_disponible=stock_inicial)
            )

    def actualizar_producto(
        self, producto_id: int, nombre: str, precio_base: int, activo: bool
    ) -> Producto:
        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del producto es obligatorio.")
        if precio_base is None or precio_base < 0:
            raise ValidacionError("El precio base no puede ser negativo.")
        with self._uow_factory() as uow:
            producto = uow.products.obtener_por_id(producto_id)
            if producto is None:
                raise ProductoNoEncontradoError(f"Producto {producto_id} no existe.")
            producto.nombre = nombre.strip()
            producto.precio_base = precio_base
            producto.activo = activo
            uow.products.actualizar(producto)
            return producto

    def ajustar_inventario(self, producto_id: int, delta: int) -> Producto:
        """Ajuste manual de inventario desde la interfaz administrativa."""
        with self._uow_factory() as uow:
            producto = uow.products.obtener_por_id(producto_id)
            if producto is None:
                raise ProductoNoEncontradoError(f"Producto {producto_id} no existe.")
            nuevo_stock = producto.stock_disponible + delta
            if nuevo_stock < 0:
                raise ValidacionError("El ajuste dejaría el stock en un valor negativo.")
            uow.products.ajustar_stock(producto_id, delta)
            producto.stock_disponible = nuevo_stock
            return producto
