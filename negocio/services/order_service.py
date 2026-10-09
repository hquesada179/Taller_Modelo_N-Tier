"""
OrderService — capa de Negocio.

Orquesta la creación y el ciclo de vida de los pedidos: valida reglas
(pedido pendiente existente, stock, redención de puntos), coordina a
StockService y LoyaltyService, y garantiza consistencia transaccional
delegando toda la persistencia a una única UnitOfWork por operación.

No contiene SQL ni HTML; no conoce el formato de transporte (JSON).
"""

from typing import Callable, List, Optional

from negocio.domain.entidades import ElementoPedido, Pedido
from negocio.domain.enums import EstadoPedido, TRANSICIONES_VALIDAS, TipoPedido
from negocio.excepciones import (
    ClienteNoEncontradoError,
    PedidoNoEncontradoError,
    PedidoPendienteExistenteError,
    ProductoNoEncontradoError,
    TransicionEstadoInvalidaError,
    ValidacionError,
)
from negocio.interfaces.repositorios import UnitOfWork
from negocio.services.discount_service import DiscountService
from negocio.services.loyalty_service import LoyaltyService
from negocio.services.stock_service import StockService


class OrderService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    # ------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------
    def obtener_pedido(self, pedido_id: int) -> Pedido:
        with self._uow_factory() as uow:
            pedido = uow.orders.obtener_por_id(pedido_id)
            if pedido is None:
                raise PedidoNoEncontradoError(f"Pedido {pedido_id} no existe.")
            return pedido

    def listar_pedidos_de_cliente(self, cliente_id: int) -> List[Pedido]:
        with self._uow_factory() as uow:
            return uow.orders.listar_por_cliente(cliente_id)

    def listar_todos_los_pedidos(self) -> List[Pedido]:
        with self._uow_factory() as uow:
            return uow.orders.listar_todos()

    def tiene_pedido_pendiente(self, cliente_id: int) -> bool:
        with self._uow_factory() as uow:
            return uow.orders.existe_pendiente_de_pago(cliente_id)

    # ------------------------------------------------------------
    # Creación de pedidos
    # ------------------------------------------------------------
    def crear_pedido(
        self,
        cliente_id: int,
        tipo_pedido: TipoPedido,
        items_solicitados: List[dict],
        numero_mesa: Optional[int] = None,
        puntos_a_redimir: int = 0,
    ) -> Pedido:
        """
        items_solicitados: lista de {"producto_id": int, "cantidad": int}
        """
        if not items_solicitados:
            raise ValidacionError("El pedido debe tener al menos un producto.")
        if tipo_pedido == TipoPedido.MESA and (numero_mesa is None or numero_mesa <= 0):
            raise ValidacionError("Un pedido en mesa requiere un número de mesa válido.")
        if tipo_pedido == TipoPedido.LLEVAR:
            numero_mesa = None

        with self._uow_factory() as uow:
            cliente = uow.customers.obtener_por_id(cliente_id)
            if cliente is None:
                raise ClienteNoEncontradoError(f"Cliente {cliente_id} no existe.")

            # Regla 4.5: un pedido pendiente de pago bloquea nuevos pedidos.
            if uow.orders.existe_pendiente_de_pago(cliente_id):
                raise PedidoPendienteExistenteError(
                    "El cliente ya tiene un pedido pendiente de pago."
                )

            # Agrupar y sumar las cantidades solicitadas POR PRODUCTO antes de
            # validar stock. Si el mismo producto aparece en varias líneas
            # (p. ej. 4 + 4 unidades con solo 5 en inventario), la validación
            # debe considerar el TOTAL solicitado, no cada línea por separado;
            # de lo contrario cada línea individual podría pasar la validación
            # y sería SQLite quien termine rechazando la operación mediante la
            # restricción CHECK (stock_disponible >= 0), lo cual pertenece a
            # la capa de negocio, no a la de persistencia.
            cantidades_por_producto = {}
            orden_productos = []
            for item in items_solicitados:
                producto_id = item["producto_id"]
                cantidad = item["cantidad"]
                StockService.validar_cantidad_positiva(cantidad)
                if producto_id not in cantidades_por_producto:
                    orden_productos.append(producto_id)
                    cantidades_por_producto[producto_id] = 0
                cantidades_por_producto[producto_id] += cantidad

            productos_por_id = {}
            subtotal = 0
            lineas = []
            for producto_id in orden_productos:
                cantidad_total = cantidades_por_producto[producto_id]
                producto = uow.products.obtener_por_id(producto_id)
                if producto is None or not producto.activo:
                    raise ProductoNoEncontradoError(f"Producto {producto_id} no existe o no está activo.")
                StockService.validar_disponibilidad(producto, cantidad_total)
                productos_por_id[producto_id] = producto
                linea_subtotal = producto.precio_base * cantidad_total
                subtotal += linea_subtotal
                lineas.append(
                    ElementoPedido(
                        id=None,
                        pedido_id=None,
                        producto_id=producto_id,
                        cantidad=cantidad_total,
                        precio_unitario=producto.precio_base,
                        subtotal=linea_subtotal,
                    )
                )

            # Descuentos (DiscountService) y redención (LoyaltyService).
            descuento_nivel = DiscountService.calcular_descuento_nivel(cliente.nivel_lealtad, subtotal)
            total_elegible = subtotal - descuento_nivel
            LoyaltyService.validar_redencion(cliente, puntos_a_redimir, total_elegible)
            descuento_devpoints = LoyaltyService.valor_en_pesos(puntos_a_redimir)
            total_calculado = total_elegible - descuento_devpoints

            pedido = Pedido(
                id=None,
                cliente_id=cliente_id,
                fecha=None,
                estado=EstadoPedido.PENDING_PAYMENT,
                subtotal=subtotal,
                descuento_nivel=descuento_nivel,
                descuento_devpoints=descuento_devpoints,
                total_calculado=total_calculado,
                devpoints_redimidos=puntos_a_redimir,
                devpoints_otorgados=0,
                beneficios_aplicados=False,
                tipo_pedido=tipo_pedido,
                numero_mesa=numero_mesa,
            )
            pedido = uow.orders.crear(pedido)

            # Persistir ítems y descontar stock de forma atómica (misma transacción).
            for linea in lineas:
                linea.pedido_id = pedido.id
                uow.order_items.crear(linea)
                StockService.descontar_stock(uow.products, linea.producto_id, linea.cantidad)
            pedido.items = lineas

            # Reservar (descontar) los DevPoints redimidos inmediatamente,
            # para evitar doble gasto del mismo saldo en pedidos concurrentes.
            if puntos_a_redimir > 0:
                cliente.saldo_devpoints -= puntos_a_redimir
                uow.customers.actualizar(cliente)

            return pedido

    # ------------------------------------------------------------
    # Transiciones de estado
    # ------------------------------------------------------------
    def cambiar_estado(self, pedido_id: int, nuevo_estado: EstadoPedido) -> Pedido:
        with self._uow_factory() as uow:
            pedido = uow.orders.obtener_por_id(pedido_id)
            if pedido is None:
                raise PedidoNoEncontradoError(f"Pedido {pedido_id} no existe.")

            transiciones_permitidas = TRANSICIONES_VALIDAS[pedido.estado]
            if nuevo_estado not in transiciones_permitidas:
                raise TransicionEstadoInvalidaError(
                    f"No se puede pasar de {pedido.estado.value} a {nuevo_estado.value}."
                )

            uow.orders.actualizar_estado(pedido_id, nuevo_estado)
            pedido.estado = nuevo_estado

            if nuevo_estado == EstadoPedido.DELIVERED:
                # Evento de finalización: se aplican los beneficios de
                # fidelización exactamente una vez (LoyaltyService
                # verifica `beneficios_aplicados` internamente).
                cliente = uow.customers.obtener_por_id(pedido.cliente_id)
                LoyaltyService.aplicar_beneficios_pedido_completado(cliente, pedido)
                uow.customers.actualizar(cliente)
                uow.orders.actualizar_totales_y_beneficios(pedido)

            return pedido
