"""
LoyaltyService — capa de Negocio.

Gestiona DevPoints (otorgamiento y redención), el monto acumulado de
compras y el ascenso automático de nivel de lealtad.

Política de cálculo (documentada explícitamente por requerimiento del
taller): tanto los DevPoints otorgados como el monto que cuenta para
el ascenso de nivel se calculan sobre el MONTO EFECTIVAMENTE PAGADO
(total_calculado, es decir, subtotal ya descontados nivel y
DevPoints), no sobre el subtotal bruto. Los umbrales de ascenso
($500.000 y $1.500.000) se evalúan sobre `monto_acumulado_compras`,
que solo se incrementa cuando un pedido llega a DELIVERED.

Política de redención: los puntos redimidos se descuentan del saldo
del cliente en el momento de CREACIÓN del pedido (ver StockService
para la política equivalente de inventario), para evitar que el mismo
saldo se redima dos veces en pedidos concurrentes. El otorgamiento de
puntos nuevos y la actualización de compras acumuladas / nivel ocurren
exclusivamente cuando el pedido pasa a DELIVERED, y exactamente una
vez por pedido (controlado por el indicador `beneficios_aplicados`).
"""

from negocio.domain.entidades import Cliente, Pedido
from negocio.domain.enums import NivelLealtad
from negocio.excepciones import RedencionInvalidaError

PESOS_POR_DEVPOINT = 20_000  # 1 DevPoint por cada $20.000 pagados
VALOR_DEVPOINT_EN_PESOS = 200  # Cada DevPoint redime $200 de descuento

UMBRAL_MID = 500_000
UMBRAL_SENIOR = 1_500_000


class LoyaltyService:
    @staticmethod
    def calcular_puntos_otorgados(monto_pagado: int) -> int:
        if monto_pagado <= 0:
            return 0
        return monto_pagado // PESOS_POR_DEVPOINT

    @staticmethod
    def valor_en_pesos(puntos: int) -> int:
        return puntos * VALOR_DEVPOINT_EN_PESOS

    @staticmethod
    def validar_redencion(cliente: Cliente, puntos_solicitados: int, total_elegible: int) -> None:
        """
        Verifica que la redención solicitada sea válida:
        - no negativa,
        - no mayor al saldo disponible del cliente,
        - su valor en pesos no supera el total elegible (subtotal tras
          el descuento de nivel) del pedido.
        """
        if puntos_solicitados is None or puntos_solicitados < 0:
            raise RedencionInvalidaError("No se pueden redimir puntos negativos.")
        if puntos_solicitados > cliente.saldo_devpoints:
            raise RedencionInvalidaError(
                f"El cliente solo dispone de {cliente.saldo_devpoints} DevPoints."
            )
        valor = LoyaltyService.valor_en_pesos(puntos_solicitados)
        if valor > total_elegible:
            raise RedencionInvalidaError(
                "El valor de los DevPoints a redimir supera el total elegible del pedido."
            )

    @staticmethod
    def evaluar_nivel(monto_acumulado_compras: int, nivel_actual: NivelLealtad) -> NivelLealtad:
        """
        Determina el nivel que corresponde al monto acumulado. El
        ascenso nunca es un retroceso: el cliente jamás desciende de
        nivel aunque el cálculo diera un nivel menor.
        """
        if monto_acumulado_compras >= UMBRAL_SENIOR:
            objetivo = NivelLealtad.SENIOR
        elif monto_acumulado_compras >= UMBRAL_MID:
            objetivo = NivelLealtad.MID
        else:
            objetivo = NivelLealtad.JUNIOR

        orden = {NivelLealtad.JUNIOR: 0, NivelLealtad.MID: 1, NivelLealtad.SENIOR: 2}
        if orden[objetivo] > orden[nivel_actual]:
            return objetivo
        return nivel_actual

    @staticmethod
    def aplicar_beneficios_pedido_completado(cliente: Cliente, pedido: Pedido) -> None:
        """
        Aplica, EXACTAMENTE UNA VEZ, los beneficios de fidelización de
        un pedido que acaba de pasar a DELIVERED: otorga DevPoints
        nuevos, acumula el monto pagado y evalúa el ascenso de nivel.

        Muta `cliente` y `pedido` en memoria; la persistencia de esos
        cambios es responsabilidad de quien invoca (OrderService).
        """
        if pedido.beneficios_aplicados:
            return  # Ya se aplicaron: evita duplicar beneficios.

        puntos_otorgados = LoyaltyService.calcular_puntos_otorgados(pedido.total_calculado)
        cliente.saldo_devpoints += puntos_otorgados
        cliente.monto_acumulado_compras += pedido.total_calculado
        cliente.nivel_lealtad = LoyaltyService.evaluar_nivel(
            cliente.monto_acumulado_compras, cliente.nivel_lealtad
        )

        pedido.devpoints_otorgados = puntos_otorgados
        pedido.beneficios_aplicados = True
