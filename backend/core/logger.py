# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE LOGGING (VERIFICADO - Compatible v3.0)
=============================================================================
Sistema de logs centralizado
Compatible con todos los módulos del sistema
"""

import os
from datetime import datetime
from pathlib import Path


# ===================================================================
# CONFIGURACIÓN
# ===================================================================

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


# ===================================================================
# CLASE DE LOGGING
# ===================================================================

class Logger:
    """Sistema centralizado de logs"""
    
    def __init__(self, archivo_base="sistema"):
        """
        Inicializa el logger
        
        Args:
            archivo_base: Nombre base del archivo de log
        """
        self.archivo_base = archivo_base
        self.fecha_actual = datetime.now().strftime('%Y-%m-%d')
        self.archivo_log = LOGS_DIR / f"{archivo_base}_{self.fecha_actual}.log"
    
    def _verificar_fecha(self):
        """Verifica si cambió la fecha y actualiza el archivo"""
        fecha_ahora = datetime.now().strftime('%Y-%m-%d')
        if fecha_ahora != self.fecha_actual:
            self.fecha_actual = fecha_ahora
            self.archivo_log = LOGS_DIR / f"{self.archivo_base}_{self.fecha_actual}.log"
    
    def _escribir_log(self, nivel, mensaje, categoria="general"):
        """
        Escribe en el log
        
        Args:
            nivel: Nivel del log (INFO, WARNING, ERROR, etc)
            mensaje: Mensaje a registrar
            categoria: Categoría del log
        """
        self._verificar_fecha()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        linea = f"[{timestamp}] [{nivel}] [{categoria}] {mensaje}\n"
        
        try:
            with open(self.archivo_log, 'a', encoding='utf-8') as f:
                f.write(linea)
        except Exception as e:
            print(f"⚠️  Error al escribir log: {e}")
    
    # ===================================================================
    # MÉTODOS DE LOGGING
    # ===================================================================
    
    def info(self, mensaje, categoria="general"):
        """Log de información"""
        self._escribir_log("INFO", mensaje, categoria)
    
    def advertencia(self, mensaje, categoria="general"):
        """Log de advertencia"""
        self._escribir_log("WARNING", mensaje, categoria)
    
    def error(self, mensaje, detalle="", categoria="general"):
        """Log de error"""
        mensaje_completo = f"{mensaje} | {detalle}" if detalle else mensaje
        self._escribir_log("ERROR", mensaje_completo, categoria)
    
    def separador(self, categoria="general"):
        """Escribe un separador en el log"""
        self._escribir_log("INFO", "="*60, categoria)
    
    # ===================================================================
    # LOGS ESPECÍFICOS DEL SISTEMA
    # ===================================================================
    
    def ciclo_creado(self, ciclo_id, dias, capital_inicial, fecha_inicio, fecha_fin):
        """Log de ciclo creado"""
        mensaje = (f"Ciclo #{ciclo_id} creado | "
                  f"Duración: {dias} días | "
                  f"Capital: ${capital_inicial:.2f} | "
                  f"Período: {fecha_inicio} → {fecha_fin}")
        self.info(mensaje, "ciclos")
    
    def ciclo_cerrado(self, ciclo_id, dias_operados, inversion_inicial, 
                     ganancia_total, capital_final):
        """Log de ciclo cerrado"""
        roi = (ganancia_total / inversion_inicial * 100) if inversion_inicial > 0 else 0
        mensaje = (f"Ciclo #{ciclo_id} cerrado | "
                  f"Días: {dias_operados} | "
                  f"Inversión: ${inversion_inicial:.2f} | "
                  f"Ganancia: ${ganancia_total:.2f} | "
                  f"Capital final: ${capital_final:.2f} | "
                  f"ROI: {roi:.2f}%")
        self.info(mensaje, "ciclos")
    
    def dia_iniciado(self, ciclo_id, dia_num, capital_inicial, criptos_disponibles):
        """Log de día iniciado"""
        criptos_str = ", ".join([f"{c[0]}: {c[1]:.8f} (${c[2]:.2f})" 
                                for c in criptos_disponibles])
        mensaje = (f"Día #{dia_num} iniciado | "
                  f"Ciclo: #{ciclo_id} | "
                  f"Capital: ${capital_inicial:.2f} | "
                  f"Criptos: {criptos_str}")
        self.info(mensaje, "operaciones")
    
    def dia_cerrado(self, ciclo_id, dia_num, capital_inicial, capital_final, 
                   ganancia_dia, ventas_realizadas):
        """Log de día cerrado"""
        roi_dia = ((capital_final - capital_inicial) / capital_inicial * 100) if capital_inicial > 0 else 0
        mensaje = (f"Día #{dia_num} cerrado | "
                  f"Ciclo: #{ciclo_id} | "
                  f"Capital inicial: ${capital_inicial:.2f} | "
                  f"Capital final: ${capital_final:.2f} | "
                  f"Ganancia: ${ganancia_dia:.2f} | "
                  f"ROI: {roi_dia:.2f}% | "
                  f"Ventas: {ventas_realizadas}")
        self.info(mensaje, "operaciones")
    
    def precio_definido(self, cripto, costo_promedio, comision, ganancia_objetivo,
                       precio_publicado, ganancia_neta_estimada):
        """Log de precio definido"""
        mensaje = (f"Precio definido para {cripto} | "
                  f"Costo: ${costo_promedio:.4f} | "
                  f"Comisión: {comision}% | "
                  f"Objetivo: {ganancia_objetivo}% | "
                  f"Precio publicado: ${precio_publicado:.4f} | "
                  f"Ganancia estimada: {ganancia_neta_estimada:.2f}%")
        self.info(mensaje, "operaciones")
    
    def venta_registrada(self, venta_num, cripto, cantidad_vendida, precio_unitario,
                        monto_total, comision_pagada, ganancia_neta):
        """Log de venta registrada"""
        mensaje = (f"Venta #{venta_num} | "
                  f"{cantidad_vendida:.8f} {cripto} | "
                  f"Precio: ${precio_unitario:.4f} | "
                  f"Total: ${monto_total:.2f} | "
                  f"Comisión: ${comision_pagada:.2f} | "
                  f"Ganancia: ${ganancia_neta:.2f}")
        self.info(mensaje, "operaciones")
    
    def boveda_compra(self, cripto, cantidad, monto_usd, tasa, ciclo_id):
        """Log de compra en bóveda"""
        mensaje = (f"Compra registrada | "
                  f"Ciclo: #{ciclo_id} | "
                  f"{cantidad:.8f} {cripto} | "
                  f"Monto: ${monto_usd:.2f} | "
                  f"Tasa: ${tasa:.4f}")
        self.info(mensaje, "boveda")
    
    def boveda_transferencia(self, cripto, cantidad, valor_usd, origen, destino):
        """Log de transferencia entre ciclos"""
        mensaje = (f"Transferencia | "
                  f"{cantidad:.8f} {cripto} | "
                  f"Valor: ${valor_usd:.2f} | "
                  f"Ciclo #{origen} → Ciclo #{destino}")
        self.info(mensaje, "boveda")


# ===================================================================
# INSTANCIA GLOBAL
# ===================================================================

log = Logger("sistema")


# ===================================================================
# TESTING
# ===================================================================

if __name__ == "__main__":
    print("="*70)
    print("TEST DEL SISTEMA DE LOGGING")
    print("="*70)
    
    # Test básico
    log.info("Test de log INFO", "test")
    log.advertencia("Test de log WARNING", "test")
    log.error("Test de log ERROR", "Detalle del error", "test")
    log.separador("test")
    
    # Test de logs específicos
    log.ciclo_creado(1, 15, 1000.0, "2025-01-01", "2025-01-15")
    log.venta_registrada(1, "USDT", 100.0, 1.0235, 102.35, 0.36, 1.99)
    
    print(f"\n✅ Logs escritos en: {log.archivo_log}")
    print("\nContenido:")
    print("-"*70)
    
    with open(log.archivo_log, 'r', encoding='utf-8') as f:
        print(f.read())
    
    print("="*70)
