"""
Entidades del dominio (capa de Negocio).

Son objetos planos de datos (dataclasses). No ejecutan SQL, no conocen
HTTP ni JSON como formato de transporte: la serialización a JSON ocurre
en la capa de Presentación a partir de estos objetos.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from negocio.domain.enums import EstadoPedido, NivelLealtad, TipoPedido


@dataclass
class Producto:
    id: Optional[int]
    nombre: str
    precio_base: int
    stock_disponible: int
    activo: bool = True


@dataclass
class Cliente:
    id: Optional[int]
    nombre: str
    correo: str
    nivel_lealtad: NivelLealtad = NivelLealtad.JUNIOR
    saldo_devpoints: int = 0
    monto_acumulado_compras: int = 0


@dataclass
class ElementoPedido:
    id: Optional[int]
    pedido_id: Optional[int]
    producto_id: int
    cantidad: int
    precio_unitario: int
    subtotal: int


@dataclass
class Pedido:
    id: Optional[int]
    cliente_id: int
    fecha: str
    estado: EstadoPedido
    subtotal: int
    descuento_nivel: int
    descuento_devpoints: int
    total_calculado: int
    devpoints_redimidos: int
    devpoints_otorgados: int
    beneficios_aplicados: bool
    tipo_pedido: TipoPedido
    numero_mesa: Optional[int] = None
    items: List[ElementoPedido] = field(default_factory=list)
