"""
Serialización de entidades de dominio a JSON.

Esta es la ÚNICA capa que conoce el formato de transporte JSON: la
capa de Negocio trabaja exclusivamente con objetos de dominio
(dataclasses de Python), nunca con diccionarios JSON.
"""

from negocio.domain.entidades import Cliente, ElementoPedido, Pedido, Producto


def producto_a_dict(p: Producto) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "precio_base": p.precio_base,
        "stock_disponible": p.stock_disponible,
        "activo": p.activo,
    }


def cliente_a_dict(c: Cliente) -> dict:
    return {
        "id": c.id,
        "nombre": c.nombre,
        "correo": c.correo,
        "nivel_lealtad": c.nivel_lealtad.value,
        "saldo_devpoints": c.saldo_devpoints,
        "monto_acumulado_compras": c.monto_acumulado_compras,
    }


def elemento_pedido_a_dict(e: ElementoPedido) -> dict:
    return {
        "id": e.id,
        "pedido_id": e.pedido_id,
        "producto_id": e.producto_id,
        "cantidad": e.cantidad,
        "precio_unitario": e.precio_unitario,
        "subtotal": e.subtotal,
    }


def pedido_a_dict(p: Pedido) -> dict:
    return {
        "id": p.id,
        "cliente_id": p.cliente_id,
        "fecha": p.fecha,
        "estado": p.estado.value,
        "subtotal": p.subtotal,
        "descuento_nivel": p.descuento_nivel,
        "descuento_devpoints": p.descuento_devpoints,
        "total_calculado": p.total_calculado,
        "devpoints_redimidos": p.devpoints_redimidos,
        "devpoints_otorgados": p.devpoints_otorgados,
        "beneficios_aplicados": p.beneficios_aplicados,
        "tipo_pedido": p.tipo_pedido.value,
        "numero_mesa": p.numero_mesa,
        "items": [elemento_pedido_a_dict(i) for i in p.items],
    }
