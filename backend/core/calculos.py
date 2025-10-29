# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE CÁLCULOS (VERIFICADO - Compatible v3.0)
=============================================================================
Todas las fórmulas y cálculos del sistema
Completamente independiente de la BD
"""

from typing import Dict, List, Tuple, Optional


class Calculadora:
    """Clase para todos los cálculos del sistema"""
    
    # ===================================================================
    # CÁLCULOS DE PRECIOS
    # ===================================================================
    
    @staticmethod
    def calcular_precio_sugerido(costo_promedio: float, 
                                 ganancia_objetivo_pct: float,
                                 comision_pct: float = 0.35) -> float:
        """
        Calcula el precio sugerido para alcanzar ganancia objetivo
        
        Args:
            costo_promedio: Costo promedio de compra
            ganancia_objetivo_pct: Ganancia neta objetivo en %
            comision_pct: Comisión de la plataforma en %
        
        Returns:
            float: Precio sugerido de venta
        """
        if costo_promedio <= 0:
            return 0
        
        # Fórmula: precio_venta = costo / (1 - (comision + ganancia)/100)
        factor = (comision_pct + ganancia_objetivo_pct) / 100
        
        if factor >= 1:
            return 0  # Imposible con estos parámetros
        
        precio_sugerido = costo_promedio / (1 - factor)
        
        return round(precio_sugerido, 4)
    
    @staticmethod
    def calcular_ganancia_neta_estimada(costo_promedio: float,
                                        precio_venta: float,
                                        comision_pct: float = 0.35) -> float:
        """
        Calcula ganancia neta estimada en porcentaje
        
        Args:
            costo_promedio: Costo promedio de compra
            precio_venta: Precio de venta publicado
            comision_pct: Comisión de la plataforma
        
        Returns:
            float: Ganancia neta en %
        """
        if costo_promedio <= 0 or precio_venta <= 0:
            return 0
        
        # Efectivo recibido después de comisión
        comision_decimal = comision_pct / 100
        efectivo_recibido = precio_venta * (1 - comision_decimal)
        
        # Ganancia neta
        ganancia_neta = efectivo_recibido - costo_promedio
        
        # Porcentaje
        ganancia_neta_pct = (ganancia_neta / costo_promedio) * 100
        
        return round(ganancia_neta_pct, 2)
    
    # ===================================================================
    # CÁLCULOS DE VENTAS
    # ===================================================================
    
    @staticmethod
    def calcular_venta(cantidad: float,
                      costo_unitario: float,
                      precio_venta: float,
                      comision_pct: float = 0.35) -> Optional[Dict]:
        """
        Calcula todos los valores de una venta
        
        Args:
            cantidad: Cantidad de cripto vendida
            costo_unitario: Costo promedio por unidad
            precio_venta: Precio de venta por unidad
            comision_pct: Comisión de la plataforma
        
        Returns:
            dict: Todos los valores calculados
        """
        if cantidad <= 0 or costo_unitario <= 0 or precio_venta <= 0:
            return None
        
        # Valores base
        costo_total = cantidad * costo_unitario
        monto_venta = cantidad * precio_venta
        
        # Comisión
        comision_decimal = comision_pct / 100
        comision = monto_venta * comision_decimal
        
        # Efectivo recibido
        efectivo_recibido = monto_venta - comision
        
        # Ganancias
        ganancia_bruta = monto_venta - costo_total
        ganancia_neta = efectivo_recibido - costo_total
        
        return {
            'cantidad': cantidad,
            'costo_unitario': costo_unitario,
            'precio_venta': precio_venta,
            'costo_total': round(costo_total, 2),
            'monto_venta': round(monto_venta, 2),
            'comision_pct': comision_pct,
            'comision': round(comision, 2),
            'efectivo_recibido': round(efectivo_recibido, 2),
            'ganancia_bruta': round(ganancia_bruta, 2),
            'ganancia_neta': round(ganancia_neta, 2)
        }
    
    # ===================================================================
    # CÁLCULOS DE CAPITAL
    # ===================================================================
    
    @staticmethod
    def calcular_capital_total(criptos: List[Tuple[str, float, float]]) -> float:
        """
        Calcula el capital total en USD
        
        Args:
            criptos: Lista de tuplas (nombre, cantidad, precio_unitario)
        
        Returns:
            float: Capital total en USD
        """
        total = 0
        for nombre, cantidad, precio in criptos:
            total += cantidad * precio
        
        return round(total, 2)
    
    @staticmethod
    def calcular_promedio_ponderado(cantidad_anterior: float,
                                    precio_anterior: float,
                                    cantidad_nueva: float,
                                    precio_nuevo: float) -> float:
        """
        Calcula precio promedio ponderado después de una compra
        
        Args:
            cantidad_anterior: Cantidad que ya tenías
            precio_anterior: Precio promedio anterior
            cantidad_nueva: Cantidad que compraste
            precio_nuevo: Precio de la nueva compra
        
        Returns:
            float: Nuevo precio promedio ponderado
        """
        if cantidad_anterior + cantidad_nueva == 0:
            return 0
        
        costo_anterior = cantidad_anterior * precio_anterior
        costo_nuevo = cantidad_nueva * precio_nuevo
        cantidad_total = cantidad_anterior + cantidad_nueva
        
        promedio = (costo_anterior + costo_nuevo) / cantidad_total
        
        return round(promedio, 4)
    
    # ===================================================================
    # CÁLCULOS DE ROI
    # ===================================================================
    
    @staticmethod
    def calcular_roi(ganancia: float, inversion: float) -> float:
        """
        Calcula ROI (Return on Investment)
        
        Args:
            ganancia: Ganancia obtenida
            inversion: Inversión inicial
        
        Returns:
            float: ROI en porcentaje
        """
        if inversion <= 0:
            return 0
        
        roi = (ganancia / inversion) * 100
        
        return round(roi, 2)
    
    @staticmethod
    def calcular_roi_diario_promedio(roi_total: float, dias: int) -> float:
        """
        Calcula ROI diario promedio
        
        Args:
            roi_total: ROI total del período
            dias: Número de días
        
        Returns:
            float: ROI promedio por día
        """
        if dias <= 0:
            return 0
        
        return round(roi_total / dias, 2)
    
    # ===================================================================
    # VALIDACIONES
    # ===================================================================
    
    @staticmethod
    def validar_precio_rentable(costo: float, 
                               precio_venta: float,
                               comision_pct: float = 0.35,
                               ganancia_minima_pct: float = 0.5) -> Tuple[bool, str]:
        """
        Valida si un precio de venta es rentable
        
        Args:
            costo: Costo de compra
            precio_venta: Precio de venta propuesto
            comision_pct: Comisión
            ganancia_minima_pct: Ganancia mínima aceptable
        
        Returns:
            tuple: (es_rentable, mensaje)
        """
        if costo <= 0 or precio_venta <= 0:
            return False, "Valores inválidos"
        
        ganancia = Calculadora.calcular_ganancia_neta_estimada(
            costo, precio_venta, comision_pct
        )
        
        if ganancia < 0:
            return False, f"Pérdida de {abs(ganancia):.2f}%"
        
        if ganancia < ganancia_minima_pct:
            return False, f"Ganancia muy baja: {ganancia:.2f}% (mínimo: {ganancia_minima_pct}%)"
        
        return True, f"Rentable: {ganancia:.2f}%"


# ===================================================================
# INSTANCIA GLOBAL
# ===================================================================

calc = Calculadora()


# ===================================================================
# TESTING
# ===================================================================

if __name__ == "__main__":
    print("="*70)
    print("TEST DEL MÓDULO DE CÁLCULOS")
    print("="*70)
    
    # Test 1: Precio sugerido
    print("\n[Test 1] Precio sugerido:")
    costo = 1.0
    ganancia_objetivo = 2.0
    precio_sugerido = calc.calcular_precio_sugerido(costo, ganancia_objetivo)
    print(f"   Costo: ${costo}")
    print(f"   Ganancia objetivo: {ganancia_objetivo}%")
    print(f"   Precio sugerido: ${precio_sugerido:.4f}")
    
    # Test 2: Ganancia estimada
    print("\n[Test 2] Ganancia neta estimada:")
    precio_venta = 1.0235
    ganancia = calc.calcular_ganancia_neta_estimada(costo, precio_venta)
    print(f"   Costo: ${costo}")
    print(f"   Precio venta: ${precio_venta}")
    print(f"   Ganancia neta: {ganancia}%")
    
    # Test 3: Cálculo de venta
    print("\n[Test 3] Cálculo completo de venta:")
    venta = calc.calcular_venta(100, 1.0, 1.0235)
    if venta:
        print(f"   Cantidad: {venta['cantidad']}")
        print(f"   Costo total: ${venta['costo_total']:.2f}")
        print(f"   Monto venta: ${venta['monto_venta']:.2f}")
        print(f"   Comisión: ${venta['comision']:.2f}")
        print(f"   Efectivo recibido: ${venta['efectivo_recibido']:.2f}")
        print(f"   Ganancia neta: ${venta['ganancia_neta']:.2f}")
    
    # Test 4: ROI
    print("\n[Test 4] Cálculo de ROI:")
    roi = calc.calcular_roi(200, 1000)
    print(f"   Ganancia: $200")
    print(f"   Inversión: $1000")
    print(f"   ROI: {roi}%")
    
    # Test 5: Validación
    print("\n[Test 5] Validar precio rentable:")
    rentable, mensaje = calc.validar_precio_rentable(1.0, 1.0235)
    print(f"   {'✅' if rentable else '❌'} {mensaje}")
    
    print("\n" + "="*70)
    print("✅ TESTS COMPLETADOS")
    print("="*70)
