# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE VALIDACIONES (COMPLETO)
=============================================================================
Validaciones centralizadas del sistema
"""

from typing import Tuple, Optional


# ===================================================================
# VALIDACIONES NUMÉRICAS
# ===================================================================

def validar_cantidad_positiva(cantidad: float, nombre: str = "cantidad") -> Tuple[bool, str]:
    """
    Valida que una cantidad sea positiva
    
    Args:
        cantidad: Valor a validar
        nombre: Nombre del campo (para mensajes)
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if cantidad <= 0:
        return False, f"La {nombre} debe ser mayor a 0"
    
    return True, ""


def validar_precio_positivo(precio: float) -> Tuple[bool, str]:
    """
    Valida que un precio sea positivo
    
    Args:
        precio: Precio a validar
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if precio <= 0:
        return False, "El precio debe ser mayor a 0"
    
    return True, ""


def validar_porcentaje(porcentaje: float, min_val: float = 0, max_val: float = 100) -> Tuple[bool, str]:
    """
    Valida que un porcentaje esté en rango válido
    
    Args:
        porcentaje: Valor a validar
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if porcentaje < min_val or porcentaje > max_val:
        return False, f"El porcentaje debe estar entre {min_val}% y {max_val}%"
    
    return True, ""


# ===================================================================
# VALIDACIONES DE OPERACIONES
# ===================================================================

def validar_venta(cantidad: float, cantidad_disponible: float, 
                  precio: float) -> Tuple[bool, str]:
    """
    Valida los parámetros de una venta
    
    Args:
        cantidad: Cantidad a vender
        cantidad_disponible: Cantidad disponible en bóveda
        precio: Precio de venta
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    # Validar cantidad
    valido, msg = validar_cantidad_positiva(cantidad)
    if not valido:
        return False, msg
    
    # Validar que hay suficiente
    if cantidad > cantidad_disponible:
        return False, f"No hay suficiente disponible (máximo: {cantidad_disponible:.8f})"
    
    # Validar precio
    valido, msg = validar_precio_positivo(precio)
    if not valido:
        return False, msg
    
    return True, ""


def validar_compra(cantidad: float, monto_usd: float, tasa: float) -> Tuple[bool, str]:
    """
    Valida los parámetros de una compra
    
    Args:
        cantidad: Cantidad a comprar
        monto_usd: Monto en USD
        tasa: Tasa de cambio
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    # Validar cantidad
    valido, msg = validar_cantidad_positiva(cantidad)
    if not valido:
        return False, msg
    
    # Validar monto
    valido, msg = validar_cantidad_positiva(monto_usd, "monto")
    if not valido:
        return False, msg
    
    # Validar tasa
    valido, msg = validar_precio_positivo(tasa)
    if not valido:
        return False, "La tasa debe ser mayor a 0"
    
    # Validar coherencia
    cantidad_esperada = monto_usd / tasa
    if abs(cantidad - cantidad_esperada) > 0.00001:  # Margen de error
        return False, "La cantidad no coincide con el monto y la tasa"
    
    return True, ""


# ===================================================================
# VALIDACIONES DE CONFIGURACIÓN
# ===================================================================

def validar_comision(comision: float) -> Tuple[bool, str]:
    """
    Valida que la comisión esté en rango razonable
    
    Args:
        comision: Comisión en porcentaje
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if comision < 0:
        return False, "La comisión no puede ser negativa"
    
    if comision > 10:
        return False, "La comisión parece muy alta (>10%)"
    
    return True, ""


def validar_ganancia_objetivo(ganancia: float) -> Tuple[bool, str]:
    """
    Valida que la ganancia objetivo sea razonable
    
    Args:
        ganancia: Ganancia objetivo en porcentaje
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if ganancia < 0:
        return False, "La ganancia objetivo no puede ser negativa"
    
    if ganancia > 20:
        return False, "La ganancia objetivo parece muy alta (>20%)"
    
    if ganancia < 0.1:
        return False, "La ganancia objetivo parece muy baja (<0.1%)"
    
    return True, ""


def validar_limites_ventas(minimo: int, maximo: int) -> Tuple[bool, str]:
    """
    Valida los límites de ventas por día
    
    Args:
        minimo: Límite mínimo
        maximo: Límite máximo
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if minimo < 1:
        return False, "El mínimo debe ser al menos 1"
    
    if maximo < minimo:
        return False, "El máximo debe ser mayor o igual al mínimo"
    
    if maximo > 20:
        return False, "El máximo parece muy alto (>20 ventas/día)"
    
    return True, ""


# ===================================================================
# VALIDACIONES DE CICLO
# ===================================================================

def validar_duracion_ciclo(dias: int) -> Tuple[bool, str]:
    """
    Valida la duración de un ciclo
    
    Args:
        dias: Número de días del ciclo
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if dias < 1:
        return False, "El ciclo debe durar al menos 1 día"
    
    if dias > 365:
        return False, "El ciclo no puede durar más de 365 días"
    
    return True, ""


def validar_capital_inicial(capital: float) -> Tuple[bool, str]:
    """
    Valida el capital inicial de un ciclo
    
    Args:
        capital: Capital inicial
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if capital <= 0:
        return False, "El capital inicial debe ser mayor a 0"
    
    if capital < 10:
        return False, "El capital inicial parece muy bajo (<$10)"
    
    return True, ""


# ===================================================================
# UTILIDADES
# ===================================================================

def es_numero_valido(valor_str: str) -> bool:
    """
    Verifica si una cadena es un número válido
    
    Args:
        valor_str: Cadena a validar
    
    Returns:
        bool: True si es un número válido
    """
    try:
        float(valor_str)
        return True
    except ValueError:
        return False


def es_entero_valido(valor_str: str) -> bool:
    """
    Verifica si una cadena es un entero válido
    
    Args:
        valor_str: Cadena a validar
    
    Returns:
        bool: True si es un entero válido
    """
    try:
        int(valor_str)
        return True
    except ValueError:
        return False


# ===================================================================
# TESTING
# ===================================================================

if __name__ == "__main__":
    print("="*70)
    print("TEST DEL MÓDULO DE VALIDACIONES")
    print("="*70)
    
    # Test 1: Cantidad positiva
    print("\n[Test 1] Validar cantidad positiva:")
    valido, msg = validar_cantidad_positiva(100)
    print(f"   100: {'✅' if valido else '❌'} {msg}")
    
    valido, msg = validar_cantidad_positiva(-10)
    print(f"   -10: {'✅' if valido else '❌'} {msg}")
    
    # Test 2: Precio
    print("\n[Test 2] Validar precio:")
    valido, msg = validar_precio_positivo(1.0235)
    print(f"   1.0235: {'✅' if valido else '❌'} {msg}")
    
    valido, msg = validar_precio_positivo(0)
    print(f"   0: {'✅' if valido else '❌'} {msg}")
    
    # Test 3: Venta
    print("\n[Test 3] Validar venta:")
    valido, msg = validar_venta(100, 1000, 1.0235)
    print(f"   Venta de 100 (disponible: 1000): {'✅' if valido else '❌'} {msg}")
    
    valido, msg = validar_venta(2000, 1000, 1.0235)
    print(f"   Venta de 2000 (disponible: 1000): {'✅' if valido else '❌'} {msg}")
    
    # Test 4: Comisión
    print("\n[Test 4] Validar comisión:")
    valido, msg = validar_comision(0.35)
    print(f"   0.35%: {'✅' if valido else '❌'} {msg}")
    
    valido, msg = validar_comision(15)
    print(f"   15%: {'✅' if valido else '❌'} {msg}")
    
    # Test 5: Ganancia objetivo
    print("\n[Test 5] Validar ganancia objetivo:")
    valido, msg = validar_ganancia_objetivo(2.0)
    print(f"   2.0%: {'✅' if valido else '❌'} {msg}")
    
    valido, msg = validar_ganancia_objetivo(25)
    print(f"   25%: {'✅' if valido else '❌'} {msg}")
    
    print("\n" + "="*70)
    print("✅ TESTS COMPLETADOS")
    print("="*70)
