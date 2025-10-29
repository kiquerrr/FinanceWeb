# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE PROYECCIONES
=============================================================================
Simulador de escenarios y calculadora de proyecciones
Ayuda a planificar ciclos y estimar resultados
"""

from typing import Dict, List
from datetime import datetime, timedelta


class CalculadoraProyecciones:
    """Calcula proyecciones y simula escenarios"""
    
    def __init__(self, capital_inicial: float, comision_pct: float = 0.35):
        """
        Inicializa calculadora
        
        Args:
            capital_inicial: Capital inicial en USD
            comision_pct: Comisión en porcentaje (ej: 0.35)
        """
        self.capital_inicial = capital_inicial
        self.comision_pct = comision_pct
    
    # ===================================================================
    # PROYECCIONES SIMPLES
    # ===================================================================
    
    def proyectar_dia_simple(self, ganancia_neta_pct: float) -> Dict:
        """
        Proyecta el resultado de un día con ganancia fija
        
        Args:
            ganancia_neta_pct: Ganancia neta objetivo (ej: 2.0 para 2%)
        
        Returns:
            dict: Resultado del día proyectado
        """
        capital_inicial = self.capital_inicial
        ganancia = capital_inicial * (ganancia_neta_pct / 100)
        capital_final = capital_inicial + ganancia
        
        return {
            'capital_inicial': capital_inicial,
            'ganancia_pct': ganancia_neta_pct,
            'ganancia_usd': ganancia,
            'capital_final': capital_final,
            'roi_dia': ganancia_neta_pct
        }
    
    def proyectar_ciclo_simple(self, dias: int, ganancia_diaria_pct: float, 
                              interes_compuesto: bool = False) -> Dict:
        """
        Proyecta un ciclo completo con ganancia diaria fija
        
        Args:
            dias: Número de días del ciclo
            ganancia_diaria_pct: Ganancia neta diaria (ej: 2.0)
            interes_compuesto: Si True, reinvierte las ganancias
        
        Returns:
            dict: Resultado del ciclo proyectado
        """
        capital = self.capital_inicial
        historial_dias = []
        ganancia_acumulada = 0
        
        for dia in range(1, dias + 1):
            ganancia_dia = capital * (ganancia_diaria_pct / 100)
            
            if interes_compuesto:
                capital += ganancia_dia
            
            ganancia_acumulada += ganancia_dia
            
            historial_dias.append({
                'dia': dia,
                'capital_inicio': capital if interes_compuesto else self.capital_inicial,
                'ganancia': ganancia_dia,
                'capital_fin': capital if interes_compuesto else self.capital_inicial,
                'ganancia_acumulada': ganancia_acumulada
            })
        
        capital_final = self.capital_inicial + ganancia_acumulada if not interes_compuesto else capital
        roi_total = (ganancia_acumulada / self.capital_inicial) * 100
        roi_promedio_diario = roi_total / dias
        
        return {
            'capital_inicial': self.capital_inicial,
            'dias_operados': dias,
            'ganancia_diaria_pct': ganancia_diaria_pct,
            'interes_compuesto': interes_compuesto,
            'ganancia_total': ganancia_acumulada,
            'capital_final': capital_final,
            'roi_total_pct': roi_total,
            'roi_promedio_diario_pct': roi_promedio_diario,
            'historial': historial_dias
        }
    
    # ===================================================================
    # PROYECCIONES AVANZADAS
    # ===================================================================
    
    def proyectar_con_variacion(self, dias: int, ganancia_min_pct: float, 
                                ganancia_max_pct: float, interes_compuesto: bool = False) -> Dict:
        """
        Proyecta con ganancia variable (mejor y peor caso)
        
        Args:
            dias: Número de días
            ganancia_min_pct: Ganancia mínima esperada
            ganancia_max_pct: Ganancia máxima esperada
            interes_compuesto: Si True, reinvierte
        
        Returns:
            dict: Escenario optimista y pesimista
        """
        ganancia_promedio = (ganancia_min_pct + ganancia_max_pct) / 2
        
        escenario_pesimista = self.proyectar_ciclo_simple(dias, ganancia_min_pct, interes_compuesto)
        escenario_promedio = self.proyectar_ciclo_simple(dias, ganancia_promedio, interes_compuesto)
        escenario_optimista = self.proyectar_ciclo_simple(dias, ganancia_max_pct, interes_compuesto)
        
        return {
            'capital_inicial': self.capital_inicial,
            'dias': dias,
            'rango_ganancia': (ganancia_min_pct, ganancia_max_pct),
            'pesimista': escenario_pesimista,
            'promedio': escenario_promedio,
            'optimista': escenario_optimista
        }
    
    def calcular_dias_para_objetivo(self, objetivo_usd: float, 
                                    ganancia_diaria_pct: float,
                                    interes_compuesto: bool = False) -> Dict:
        """
        Calcula cuántos días se necesitan para alcanzar un objetivo
        
        Args:
            objetivo_usd: Objetivo de ganancia en USD
            ganancia_diaria_pct: Ganancia diaria esperada
            interes_compuesto: Si se reinvierte
        
        Returns:
            dict: Días necesarios y proyección
        """
        if objetivo_usd <= 0:
            return {'error': 'Objetivo debe ser mayor a 0'}
        
        capital = self.capital_inicial
        ganancia_acumulada = 0
        dias = 0
        max_dias = 1000  # Límite de seguridad
        
        while ganancia_acumulada < objetivo_usd and dias < max_dias:
            dias += 1
            ganancia_dia = capital * (ganancia_diaria_pct / 100)
            ganancia_acumulada += ganancia_dia
            
            if interes_compuesto:
                capital += ganancia_dia
        
        if dias >= max_dias:
            return {'error': 'Objetivo inalcanzable con parámetros dados'}
        
        return {
            'objetivo_usd': objetivo_usd,
            'dias_necesarios': dias,
            'ganancia_diaria_pct': ganancia_diaria_pct,
            'capital_inicial': self.capital_inicial,
            'capital_final': capital,
            'ganancia_total': ganancia_acumulada,
            'interes_compuesto': interes_compuesto
        }
    
    def comparar_estrategias(self, dias: int, ganancia_pct: float) -> Dict:
        """
        Compara resultados con y sin interés compuesto
        
        Args:
            dias: Días del ciclo
            ganancia_pct: Ganancia diaria
        
        Returns:
            dict: Comparación de estrategias
        """
        sin_compuesto = self.proyectar_ciclo_simple(dias, ganancia_pct, False)
        con_compuesto = self.proyectar_ciclo_simple(dias, ganancia_pct, True)
        
        diferencia = con_compuesto['ganancia_total'] - sin_compuesto['ganancia_total']
        ventaja_pct = (diferencia / sin_compuesto['ganancia_total']) * 100
        
        return {
            'capital_inicial': self.capital_inicial,
            'dias': dias,
            'ganancia_diaria_pct': ganancia_pct,
            'sin_compuesto': {
                'ganancia_total': sin_compuesto['ganancia_total'],
                'capital_final': sin_compuesto['capital_final'],
                'roi_pct': sin_compuesto['roi_total_pct']
            },
            'con_compuesto': {
                'ganancia_total': con_compuesto['ganancia_total'],
                'capital_final': con_compuesto['capital_final'],
                'roi_pct': con_compuesto['roi_total_pct']
            },
            'diferencia_usd': diferencia,
            'ventaja_compuesto_pct': ventaja_pct
        }
    
    # ===================================================================
    # ANÁLISIS DE RIESGO
    # ===================================================================
    
    def calcular_punto_equilibrio(self, costo_operacion_diario: float = 0) -> Dict:
        """
        Calcula ganancia mínima diaria para cubrir costos
        
        Args:
            costo_operacion_diario: Costo fijo diario en USD
        
        Returns:
            dict: Punto de equilibrio
        """
        if costo_operacion_diario == 0:
            return {
                'costo_diario': 0,
                'ganancia_minima_pct': 0,
                'mensaje': 'Sin costos fijos, cualquier ganancia es beneficio'
            }
        
        ganancia_minima_pct = (costo_operacion_diario / self.capital_inicial) * 100
        
        return {
            'capital_inicial': self.capital_inicial,
            'costo_diario': costo_operacion_diario,
            'ganancia_minima_pct': ganancia_minima_pct,
            'ganancia_minima_usd': costo_operacion_diario,
            'mensaje': f'Necesitas al menos {ganancia_minima_pct:.2f}% diario para cubrir costos'
        }
    
    def calcular_perdida_maxima(self, dias_sin_operar: int, ganancia_diaria_esperada_pct: float) -> Dict:
        """
        Calcula pérdida por días sin operar
        
        Args:
            dias_sin_operar: Días que no se operará
            ganancia_diaria_esperada_pct: Ganancia que se dejaría de ganar
        
        Returns:
            dict: Costo de oportunidad
        """
        ganancia_por_dia = self.capital_inicial * (ganancia_diaria_esperada_pct / 100)
        perdida_total = ganancia_por_dia * dias_sin_operar
        
        return {
            'capital_inicial': self.capital_inicial,
            'dias_sin_operar': dias_sin_operar,
            'ganancia_diaria_esperada': ganancia_por_dia,
            'costo_oportunidad': perdida_total,
            'mensaje': f'Dejarías de ganar ${perdida_total:.2f} en {dias_sin_operar} días'
        }


# ===================================================================
# FUNCIONES DE INTERFAZ
# ===================================================================

def menu_proyecciones():
    """Menú interactivo de proyecciones"""
    
    print("\n" + "="*60)
    print("CALCULADORA DE PROYECCIONES")
    print("="*60)
    
    # Solicitar capital inicial
    try:
        capital = float(input("\nCapital inicial (USD): $"))
        if capital <= 0:
            print("❌ Capital debe ser mayor a 0")
            return
    except ValueError:
        print("❌ Valor inválido")
        return
    
    calc = CalculadoraProyecciones(capital)
    
    while True:
        print("\n" + "="*60)
        print("OPCIONES DE PROYECCIÓN")
        print("="*60)
        print("[1] Proyectar un día")
        print("[2] Proyectar ciclo completo")
        print("[3] Comparar con/sin interés compuesto")
        print("[4] Calcular días para objetivo")
        print("[5] Escenarios (optimista/pesimista)")
        print("[6] Punto de equilibrio")
        print("[7] Costo de oportunidad")
        print("[8] Volver")
        print("="*60)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            proyectar_dia_interactivo(calc)
        elif opcion == "2":
            proyectar_ciclo_interactivo(calc)
        elif opcion == "3":
            comparar_estrategias_interactivo(calc)
        elif opcion == "4":
            calcular_dias_objetivo_interactivo(calc)
        elif opcion == "5":
            proyectar_escenarios_interactivo(calc)
        elif opcion == "6":
            punto_equilibrio_interactivo(calc)
        elif opcion == "7":
            costo_oportunidad_interactivo(calc)
        elif opcion == "8":
            break
        else:
            print("❌ Opción inválida")


def proyectar_dia_interactivo(calc: CalculadoraProyecciones):
    """Proyección de un día"""
    try:
        ganancia = float(input("\nGanancia neta esperada (%): "))
        
        resultado = calc.proyectar_dia_simple(ganancia)
        
        print("\n" + "="*60)
        print("PROYECCIÓN DE UN DÍA")
        print("="*60)
        print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
        print(f"Ganancia esperada: {resultado['ganancia_pct']:.2f}%")
        print(f"Ganancia en USD: ${resultado['ganancia_usd']:.2f}")
        print(f"Capital final: ${resultado['capital_final']:.2f}")
        print("="*60)
        
    except ValueError:
        print("❌ Valor inválido")
    
    input("\nPresiona Enter...")


def proyectar_ciclo_interactivo(calc: CalculadoraProyecciones):
    """Proyección de ciclo completo"""
    try:
        dias = int(input("\n¿Cuántos días durará el ciclo?: "))
        ganancia = float(input("Ganancia diaria esperada (%): "))
        compuesto = input("¿Aplicar interés compuesto? (s/n): ").lower() == 's'
        
        resultado = calc.proyectar_ciclo_simple(dias, ganancia, compuesto)
        
        print("\n" + "="*60)
        print("PROYECCIÓN DEL CICLO")
        print("="*60)
        print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
        print(f"Días: {resultado['dias_operados']}")
        print(f"Ganancia diaria: {resultado['ganancia_diaria_pct']:.2f}%")
        print(f"Interés compuesto: {'Sí' if resultado['interes_compuesto'] else 'No'}")
        print(f"\nGanancia total: ${resultado['ganancia_total']:.2f}")
        print(f"Capital final: ${resultado['capital_final']:.2f}")
        print(f"ROI total: {resultado['roi_total_pct']:.2f}%")
        print(f"ROI promedio diario: {resultado['roi_promedio_diario_pct']:.2f}%")
        
        # Mostrar algunos días del historial
        print(f"\n--- Primeros 5 días ---")
        for dia in resultado['historial'][:5]:
            print(f"Día {dia['dia']}: Ganancia ${dia['ganancia']:.2f} | Acumulado ${dia['ganancia_acumulada']:.2f}")
        
        if len(resultado['historial']) > 10:
            print(f"\n--- Últimos 5 días ---")
            for dia in resultado['historial'][-5:]:
                print(f"Día {dia['dia']}: Ganancia ${dia['ganancia']:.2f} | Acumulado ${dia['ganancia_acumulada']:.2f}")
        
        print("="*60)
        
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter...")


def comparar_estrategias_interactivo(calc: CalculadoraProyecciones):
    """Comparación de estrategias"""
    try:
        dias = int(input("\nDías del ciclo: "))
        ganancia = float(input("Ganancia diaria (%): "))
        
        resultado = calc.comparar_estrategias(dias, ganancia)
        
        print("\n" + "="*60)
        print("COMPARACIÓN: CON vs SIN INTERÉS COMPUESTO")
        print("="*60)
        print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
        print(f"Días: {resultado['dias']}")
        print(f"Ganancia diaria: {resultado['ganancia_diaria_pct']:.2f}%")
        
        print(f"\n📊 SIN INTERÉS COMPUESTO:")
        print(f"   Ganancia total: ${resultado['sin_compuesto']['ganancia_total']:.2f}")
        print(f"   Capital final: ${resultado['sin_compuesto']['capital_final']:.2f}")
        print(f"   ROI: {resultado['sin_compuesto']['roi_pct']:.2f}%")
        
        print(f"\n📈 CON INTERÉS COMPUESTO:")
        print(f"   Ganancia total: ${resultado['con_compuesto']['ganancia_total']:.2f}")
        print(f"   Capital final: ${resultado['con_compuesto']['capital_final']:.2f}")
        print(f"   ROI: {resultado['con_compuesto']['roi_pct']:.2f}%")
        
        print(f"\n💰 VENTAJA DEL INTERÉS COMPUESTO:")
        print(f"   Diferencia: ${resultado['diferencia_usd']:.2f}")
        print(f"   Ventaja: {resultado['ventaja_compuesto_pct']:.2f}% más ganancia")
        print("="*60)
        
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter...")


def calcular_dias_objetivo_interactivo(calc: CalculadoraProyecciones):
    """Calcular días para alcanzar objetivo"""
    try:
        objetivo = float(input("\nObjetivo de ganancia (USD): $"))
        ganancia = float(input("Ganancia diaria esperada (%): "))
        compuesto = input("¿Con interés compuesto? (s/n): ").lower() == 's'
        
        resultado = calc.calcular_dias_para_objetivo(objetivo, ganancia, compuesto)
        
        if 'error' in resultado:
            print(f"\n❌ {resultado['error']}")
        else:
            print("\n" + "="*60)
            print("DÍAS NECESARIOS PARA OBJETIVO")
            print("="*60)
            print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
            print(f"Objetivo: ${resultado['objetivo_usd']:.2f}")
            print(f"Ganancia diaria: {resultado['ganancia_diaria_pct']:.2f}%")
            print(f"Interés compuesto: {'Sí' if resultado['interes_compuesto'] else 'No'}")
            print(f"\n⏱️  Días necesarios: {resultado['dias_necesarios']}")
            print(f"Capital final: ${resultado['capital_final']:.2f}")
            print(f"Ganancia total: ${resultado['ganancia_total']:.2f}")
            print("="*60)
        
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter...")


def proyectar_escenarios_interactivo(calc: CalculadoraProyecciones):
    """Escenarios optimista y pesimista"""
    try:
        dias = int(input("\nDías del ciclo: "))
        ganancia_min = float(input("Ganancia mínima esperada (%): "))
        ganancia_max = float(input("Ganancia máxima esperada (%): "))
        compuesto = input("¿Con interés compuesto? (s/n): ").lower() == 's'
        
        resultado = calc.proyectar_con_variacion(dias, ganancia_min, ganancia_max, compuesto)
        
        print("\n" + "="*60)
        print("ESCENARIOS DE PROYECCIÓN")
        print("="*60)
        print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
        print(f"Días: {resultado['dias']}")
        print(f"Rango ganancia: {resultado['rango_ganancia'][0]:.2f}% - {resultado['rango_ganancia'][1]:.2f}%")
        
        print(f"\n😰 ESCENARIO PESIMISTA ({ganancia_min}% diario):")
        print(f"   Ganancia: ${resultado['pesimista']['ganancia_total']:.2f}")
        print(f"   Capital final: ${resultado['pesimista']['capital_final']:.2f}")
        print(f"   ROI: {resultado['pesimista']['roi_total_pct']:.2f}%")
        
        print(f"\n😐 ESCENARIO PROMEDIO ({(ganancia_min+ganancia_max)/2:.2f}% diario):")
        print(f"   Ganancia: ${resultado['promedio']['ganancia_total']:.2f}")
        print(f"   Capital final: ${resultado['promedio']['capital_final']:.2f}")
        print(f"   ROI: {resultado['promedio']['roi_total_pct']:.2f}%")
        
        print(f"\n🤑 ESCENARIO OPTIMISTA ({ganancia_max}% diario):")
        print(f"   Ganancia: ${resultado['optimista']['ganancia_total']:.2f}")
        print(f"   Capital final: ${resultado['optimista']['capital_final']:.2f}")
        print(f"   ROI: {resultado['optimista']['roi_total_pct']:.2f}%")
        
        print("="*60)
        
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter...")


def punto_equilibrio_interactivo(calc: CalculadoraProyecciones):
    """Calcular punto de equilibrio"""
    try:
        costo = float(input("\nCosto fijo diario (USD, 0 si no hay): $"))
        
        resultado = calc.calcular_punto_equilibrio(costo)
        
        print("\n" + "="*60)
        print("PUNTO DE EQUILIBRIO")
        print("="*60)
        print(f"Capital inicial: ${resultado.get('capital_inicial', calc.capital_inicial):.2f}")
        print(f"Costo diario: ${resultado['costo_diario']:.2f}")
        
        if resultado['ganancia_minima_pct'] > 0:
            print(f"\n⚖️  Ganancia mínima necesaria:")
            print(f"   {resultado['ganancia_minima_pct']:.2f}% diario")
            print(f"   ${resultado['ganancia_minima_usd']:.2f} USD diario")
        
        print(f"\n💡 {resultado['mensaje']}")
        print("="*60)
        
    except ValueError:
        print("❌ Valor inválido")
    
    input("\nPresiona Enter...")


def costo_oportunidad_interactivo(calc: CalculadoraProyecciones):
    """Calcular costo de oportunidad"""
    try:
        dias = int(input("\nDías sin operar: "))
        ganancia = float(input("Ganancia diaria que dejarías de ganar (%): "))
        
        resultado = calc.calcular_perdida_maxima(dias, ganancia)
        
        print("\n" + "="*60)
        print("COSTO DE OPORTUNIDAD")
        print("="*60)
        print(f"Capital inicial: ${resultado['capital_inicial']:.2f}")
        print(f"Días sin operar: {resultado['dias_sin_operar']}")
        print(f"Ganancia diaria esperada: ${resultado['ganancia_diaria_esperada']:.2f}")
        print(f"\n💸 Costo de oportunidad: ${resultado['costo_oportunidad']:.2f}")
        print(f"\n⚠️  {resultado['mensaje']}")
        print("="*60)
        
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter...")


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_proyecciones()
