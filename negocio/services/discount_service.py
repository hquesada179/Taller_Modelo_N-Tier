"""
DiscountService — capa de Negocio.

Centraliza los porcentajes de descuento por nivel de lealtad y el
cálculo de totales de un pedido. No ejecuta SQL ni conoce HTTP.

Todos los montos son enteros (pesos colombianos). El descuento se
calcula con división entera (floor) para evitar fracciones de peso.
"""

from negocio.domain.enums import NivelLealtad


class DiscountService:
    # Porcentajes de descuento centralizados por nivel de lealtad.
    PORCENTAJES = {
        NivelLealtad.JUNIOR: 5,
        NivelLealtad.MID: 10,
        NivelLealtad.SENIOR: 15,
    }

    @classmethod
    def porcentaje_para_nivel(cls, nivel: NivelLealtad) -> int:
        return cls.PORCENTAJES[nivel]

    @classmethod
    def calcular_descuento_nivel(cls, nivel: NivelLealtad, subtotal: int) -> int:
        """Descuento (en pesos) aplicado sobre el subtotal según el nivel."""
        porcentaje = cls.porcentaje_para_nivel(nivel)
        return (subtotal * porcentaje) // 100

    @staticmethod
    def calcular_descuento_devpoints(puntos: int, valor_por_punto: int) -> int:
        return puntos * valor_por_punto

    @classmethod
    def calcular_totales(cls, subtotal: int, nivel: NivelLealtad, descuento_devpoints: int) -> dict:
        """
        Calcula el desglose completo de un pedido.

        Devuelve un diccionario con subtotal, descuento_nivel,
        descuento_devpoints y total_calculado. El total nunca es
        negativo.
        """
        descuento_nivel = cls.calcular_descuento_nivel(nivel, subtotal)
        restante_tras_nivel = subtotal - descuento_nivel
        descuento_devpoints = min(descuento_devpoints, restante_tras_nivel)
        total = restante_tras_nivel - descuento_devpoints
        return {
            "subtotal": subtotal,
            "descuento_nivel": descuento_nivel,
            "descuento_devpoints": descuento_devpoints,
            "total_calculado": max(total, 0),
        }
