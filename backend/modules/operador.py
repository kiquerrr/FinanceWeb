# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO OPERADOR (CORREGIDO v3.1)
=============================================================================
Gestión completa de operaciones diarias
CORRECCIONES:
- Actualiza bóveda al registrar ventas
- Cierre de día con conteo correcto de ventas
- Alertas de límite de ventas funcionando
"""

from datetime import datetime
from typing import Optional, Dict, List
from core.db_manager import db
from core.logger import log
from core.calculos import calc
from core.queries import queries
from core.validaciones import validar_cantidad_positiva, validar_precio_positivo


# ===================================================================
# FUNCIONES DE GESTIÓN DE VENTAS
# ===================================================================

def registrar_venta_manual(dia_id: int, cripto_id: int, cantidad: float,
                           precio_unitario: float, comision_pct: float) -> int:
    """
    Registra una venta y actualiza la bóveda
    
    Args:
        dia_id: ID del día
        cripto_id: ID de la criptomoneda
        cantidad: Cantidad vendida
        precio_unitario: Precio de venta por unidad
        comision_pct: Comisión de la plataforma
    
    Returns:
        int: ID de la venta registrada
    """
    
    # Obtener precio promedio de la bóveda
    dia = db.execute_query(
        "SELECT ciclo_id FROM dias WHERE id = ?",
        (dia_id,),
        fetch_one=True
    )
    
    boveda = db.execute_query("""
        SELECT precio_promedio FROM boveda_ciclo
        WHERE ciclo_id = ? AND cripto_id = ?
    """, (dia['ciclo_id'], cripto_id), fetch_one=True)
    
    if not boveda:
        raise ValueError("No hay criptos en bóveda")
    
    costo_unitario = boveda['precio_promedio']
    
    # Calcular venta usando el módulo de cálculos
    venta_calculada = calc.calcular_venta(
        cantidad, costo_unitario, precio_unitario, comision_pct
    )
    
    if not venta_calculada:
        raise ValueError("Error al calcular la venta")
    
    # Insertar venta en BD
    venta_id = db.execute_update("""
        INSERT INTO ventas (
            dia_id, cripto_id, cantidad, precio_unitario,
            costo_total, monto_venta, comision, efectivo_recibido,
            ganancia_bruta, ganancia_neta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dia_id,
        cripto_id,
        cantidad,
        precio_unitario,
        venta_calculada['costo_total'],
        venta_calculada['monto_venta'],
        venta_calculada['comision'],
        venta_calculada['efectivo_recibido'],
        venta_calculada['ganancia_bruta'],
        venta_calculada['ganancia_neta']
    ))
    
    # ⭐ CRÍTICO: ACTUALIZAR BÓVEDA
    with db.get_cursor(commit=True) as cursor:
        # Restar cantidad de la bóveda
        cursor.execute("""
            UPDATE boveda_ciclo
            SET cantidad = cantidad - ?
            WHERE ciclo_id = ? AND cripto_id = ?
        """, (cantidad, dia['ciclo_id'], cripto_id))
        
        # Verificar que no quedó negativa
        cursor.execute("""
            SELECT cantidad FROM boveda_ciclo
            WHERE ciclo_id = ? AND cripto_id = ?
        """, (dia['ciclo_id'], cripto_id))
        
        result = cursor.fetchone()
        if result and result['cantidad'] < 0:
            # Rollback automático por el context manager
            raise ValueError("Error: cantidad en bóveda insuficiente")
    
    # Actualizar totales del día
    with db.get_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE dias
            SET efectivo_recibido = efectivo_recibido + ?,
                comisiones_pagadas = comisiones_pagadas + ?,
                ganancia_bruta = ganancia_bruta + ?,
                ganancia_neta = ganancia_neta + ?
            WHERE id = ?
        """, (
            venta_calculada['efectivo_recibido'],
            venta_calculada['comision'],
            venta_calculada['ganancia_bruta'],
            venta_calculada['ganancia_neta'],
            dia_id
        ))
    
    # Log
    cripto = db.execute_query(
        "SELECT simbolo FROM criptomonedas WHERE id = ?",
        (cripto_id,),
        fetch_one=True
    )
    
    log.venta_registrada(
        venta_id,
        cripto['simbolo'],
        cantidad,
        precio_unitario,
        venta_calculada['monto_venta'],
        venta_calculada['comision'],
        venta_calculada['ganancia_neta']
    )
    
    return venta_id


def obtener_cantidad_disponible(ciclo_id: int, cripto_id: int) -> float:
    """
    Obtiene cantidad disponible REAL en la bóveda
    
    Args:
        ciclo_id: ID del ciclo
        cripto_id: ID de la cripto
    
    Returns:
        float: Cantidad disponible
    """
    boveda = db.execute_query("""
        SELECT cantidad FROM boveda_ciclo
        WHERE ciclo_id = ? AND cripto_id = ?
    """, (ciclo_id, cripto_id), fetch_one=True)
    
    return boveda['cantidad'] if boveda else 0


# ===================================================================
# FUNCIONES DE GESTIÓN DE DÍAS
# ===================================================================

def iniciar_dia_operacion(ciclo_id: int, capital_inicial: float) -> int:
    """
    Inicia un nuevo día de operación
    
    Args:
        ciclo_id: ID del ciclo
        capital_inicial: Capital disponible
    
    Returns:
        int: ID del día creado
    """
    
    # Obtener número del día
    ultimo_dia = db.execute_query("""
        SELECT MAX(numero_dia) as ultimo
        FROM dias WHERE ciclo_id = ?
    """, (ciclo_id,), fetch_one=True)
    
    numero_dia = (ultimo_dia['ultimo'] or 0) + 1
    
    # Crear día
    dia_id = db.execute_update("""
        INSERT INTO dias (
            ciclo_id, numero_dia, capital_inicial, estado
        ) VALUES (?, ?, ?, 'abierto')
    """, (ciclo_id, numero_dia, capital_inicial))
    
    log.info(f"Día #{numero_dia} iniciado en ciclo #{ciclo_id} con ${capital_inicial:.2f}", 
             categoria='operaciones')
    
    return dia_id


def cerrar_dia_operacion(dia_id: int) -> bool:
    """
    Cierra el día de operación
    
    Args:
        dia_id: ID del día a cerrar
    
    Returns:
        bool: True si se cerró correctamente
    """
    
    # Obtener día
    dia = db.execute_query(
        "SELECT * FROM dias WHERE id = ?",
        (dia_id,),
        fetch_one=True
    )
    
    if not dia:
        print("❌ Día no encontrado")
        return False
    
    if dia['estado'] == 'cerrado':
        print("⚠️  Este día ya está cerrado")
        return False
    
    # ⭐ OBTENER VENTAS DEL DÍA
    ventas = db.execute_query("""
        SELECT * FROM ventas WHERE dia_id = ?
    """, (dia_id,))
    
    num_ventas = len(ventas) if ventas else 0
    
    # Advertencia si no hay ventas
    if num_ventas == 0:
        print("\n⚠️  No hay ventas registradas en este día")
        confirmar = input("    ¿Deseas cerrar el día sin ventas?\n    (s/n): ").lower()
        if confirmar != 's':
            print("❌ Cierre cancelado")
            return False
    
    # Calcular totales desde las ventas
    efectivo_total = sum(v['efectivo_recibido'] for v in ventas) if ventas else 0
    comisiones_total = sum(v['comision'] for v in ventas) if ventas else 0
    ganancia_bruta_total = sum(v['ganancia_bruta'] for v in ventas) if ventas else 0
    ganancia_neta_total = sum(v['ganancia_neta'] for v in ventas) if ventas else 0
    
    # Capital final
    capital_final = dia['capital_inicial'] + ganancia_neta_total
    
    # ⭐ ACTUALIZAR DÍA
    db.execute_update("""
        UPDATE dias
        SET capital_final = ?,
            efectivo_recibido = ?,
            comisiones_pagadas = ?,
            ganancia_bruta = ?,
            ganancia_neta = ?,
            estado = 'cerrado',
            fecha_cierre = ?
        WHERE id = ?
    """, (capital_final, efectivo_total, comisiones_total,
          ganancia_bruta_total, ganancia_neta_total, datetime.now(), dia_id))
    
    # Actualizar ciclo
    with db.get_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE ciclos
            SET dias_operados = dias_operados + 1,
                ganancia_total = ganancia_total + ?
            WHERE id = ?
        """, (ganancia_neta_total, dia['ciclo_id']))
    
    # Mostrar resumen
    print("\n" + "="*60)
    print(f"DÍA #{dia['numero_dia']} CERRADO")
    print("="*60)
    print(f"\nCapital inicial: ${dia['capital_inicial']:.2f}")
    print(f"Capital final: ${capital_final:.2f}")
    print(f"Efectivo recibido: ${efectivo_total:.2f}")
    print(f"Comisiones pagadas: ${comisiones_total:.2f}")
    print(f"Ganancia bruta: ${ganancia_bruta_total:.2f}")
    print(f"Ganancia neta: ${ganancia_neta_total:.2f}")
    print(f"Ventas realizadas: {num_ventas}")
    print("="*60)
    
    # Log
    log.dia_cerrado(
        dia['ciclo_id'],
        dia['numero_dia'],
        dia['capital_inicial'],
        capital_final,
        ganancia_neta_total,
        num_ventas
    )
    
    print("\n✅ Día cerrado exitosamente")
    
    return True


def aplicar_interes_compuesto(ciclo_id: int) -> bool:
    """
    Aplica interés compuesto reinvirtiendo la ganancia del día
    
    Args:
        ciclo_id: ID del ciclo
    
    Returns:
        bool: True si se aplicó correctamente
    """
    
    # Obtener último día cerrado
    ultimo_dia = db.execute_query("""
        SELECT * FROM dias
        WHERE ciclo_id = ? AND estado = 'cerrado'
        ORDER BY numero_dia DESC
        LIMIT 1
    """, (ciclo_id,), fetch_one=True)
    
    if not ultimo_dia:
        print("❌ No hay días cerrados en este ciclo")
        return False
    
    efectivo = ultimo_dia['efectivo_recibido'] or 0
    
    if efectivo <= 0:
        print("⚠️  No hay efectivo para reinvertir")
        return False
    
    print(f"\n💰 Efectivo disponible: ${efectivo:.2f}")
    
    # Mostrar criptos disponibles
    criptos = db.execute_query("""
        SELECT id, nombre, simbolo FROM criptomonedas
        ORDER BY nombre
    """)
    
    print("\n¿En qué cripto deseas reinvertir?")
    for i, cripto in enumerate(criptos, 1):
        print(f"[{i}] {cripto['nombre']} ({cripto['simbolo']})")
    
    try:
        opcion = int(input("\nSelecciona: "))
        if opcion < 1 or opcion > len(criptos):
            print("❌ Opción inválida")
            return False
        
        cripto_seleccionada = criptos[opcion - 1]
        
        # Pedir tasa de compra
        tasa_str = input(f"\n¿A qué tasa compraste {cripto_seleccionada['simbolo']}?: ")
        tasa = float(tasa_str)
        
        if tasa <= 0:
            print("❌ Tasa inválida")
            return False
        
        # Calcular cantidad
        cantidad = efectivo / tasa
        
        print(f"\n📈 Comprarás {cantidad:.8f} {cripto_seleccionada['simbolo']}")
        confirmar = input("¿Confirmar? (s/n): ").lower()
        
        if confirmar != 's':
            print("❌ Operación cancelada")
            return False
        
        # Registrar compra
        compra_id = db.execute_update("""
            INSERT INTO compras (
                ciclo_id, cripto_id, cantidad, monto_usd, tasa
            ) VALUES (?, ?, ?, ?, ?)
        """, (ciclo_id, cripto_seleccionada['id'], cantidad, efectivo, tasa))
        
        # Actualizar bóveda
        with db.get_cursor(commit=True) as cursor:
            # Verificar si ya existe
            cursor.execute("""
                SELECT cantidad, precio_promedio
                FROM boveda_ciclo
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (ciclo_id, cripto_seleccionada['id']))
            
            boveda_actual = cursor.fetchone()
            
            if boveda_actual:
                # Calcular nuevo promedio ponderado
                nuevo_promedio = calc.calcular_promedio_ponderado(
                    boveda_actual['cantidad'],
                    boveda_actual['precio_promedio'],
                    cantidad,
                    tasa
                )
                
                cursor.execute("""
                    UPDATE boveda_ciclo
                    SET cantidad = cantidad + ?,
                        precio_promedio = ?
                    WHERE ciclo_id = ? AND cripto_id = ?
                """, (cantidad, nuevo_promedio, ciclo_id, cripto_seleccionada['id']))
            else:
                # Crear nueva entrada
                cursor.execute("""
                    INSERT INTO boveda_ciclo (
                        ciclo_id, cripto_id, cantidad, precio_promedio
                    ) VALUES (?, ?, ?, ?)
                """, (ciclo_id, cripto_seleccionada['id'], cantidad, tasa))
        
        print(f"\n✅ Interés compuesto aplicado")
        print(f"   {cantidad:.8f} {cripto_seleccionada['simbolo']} añadidos a la bóveda")
        
        log.boveda_compra(
            cripto_seleccionada['simbolo'],
            cantidad,
            efectivo,
            tasa,
            ciclo_id
        )
        
        return True
        
    except ValueError:
        print("❌ Valor inválido")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        log.error("Error al aplicar interés compuesto", str(e))
        return False


# ===================================================================
# FLUJO PRINCIPAL DE OPERACIÓN
# ===================================================================

def modulo_operador():
    """Módulo principal de operación diaria"""
    
    print("\n" + "="*60)
    print("MODULO OPERADOR: INICIANDO DIA DE OPERACION")
    print("="*60)
    
    # Verificar ciclo activo
    ciclo = queries.obtener_ciclo_activo()
    
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        print("   Crea un ciclo primero en: Gestión > Ciclos")
        input("\nPresiona Enter...")
        return
    
    # Mostrar info del ciclo
    print(f"\n📈 Ciclo activo: #{ciclo['id']}")
    print(f"    Estado: {ciclo['estado'].upper()}")
    print(f"    Duración: {ciclo['dias_planificados']} días")
    
    dias_restantes = ciclo['dias_planificados'] - ciclo['dias_operados']
    print(f"    Transcurridos: {ciclo['dias_operados']} días")
    print(f"    Restantes: {dias_restantes} días")
    print(f"    Inversión inicial: ${ciclo['inversion_inicial']:.2f}")
    
    # Verificar si hay día abierto
    dia_abierto = queries.obtener_dia_abierto(ciclo['id'])
    
    if dia_abierto:
        print(f"\n⚠️  Ya hay un día abierto: Día #{dia_abierto['numero_dia']}")
        continuar = input("¿Deseas continuar con este día? (s/n): ").lower()
        
        if continuar != 's':
            print("❌ Operación cancelada")
            input("\nPresiona Enter...")
            return
        
        dia_id = dia_abierto['id']
        capital_inicial = dia_abierto['capital_inicial']
        
    else:
        # Iniciar nuevo día
        capital_boveda = queries.obtener_capital_boveda(ciclo['id'])
        
        print(f"\nIniciando nuevo dia de operacion...")
        dia_id = iniciar_dia_operacion(ciclo['id'], capital_boveda)
        capital_inicial = capital_boveda
        numero_dia_nuevo = db.execute_query('SELECT numero_dia FROM dias WHERE id = ?', (dia_id,), fetch_one=True)['numero_dia']
        print(f"✅ Día #{numero_dia_nuevo} iniciado con ${capital_inicial:.2f}")
    
    # Obtener número de día
    dia = db.execute_query(
        "SELECT numero_dia FROM dias WHERE id = ?",
        (dia_id,),
        fetch_one=True
    )
    
    print(f"\nDia de operacion #{dia['numero_dia']}")
    print(f"Capital inicial del dia: ${capital_inicial:.2f}")
    
    # Mostrar capital disponible por cripto
    criptos_disponibles = queries.obtener_criptos_boveda(ciclo['id'])
    
    if not criptos_disponibles:
        print("\n❌ No hay criptos en la bóveda")
        print("   Fondea la bóveda primero en: Gestión > Bóveda")
        input("\nPresiona Enter...")
        return
    
    print("\nCapital actual:")
    total_capital = 0
    for cripto in criptos_disponibles:
        print(f"  - {cripto['cantidad']:.8f} {cripto['nombre']} ({cripto['simbolo']}) = ${cripto['valor_usd']:.2f}")
        total_capital += cripto['valor_usd']
    print(f"  Total: ${total_capital:.2f} USD")
    
    # Seleccionar cripto para operar
    print("\n¿Con cual cripto deseas operar hoy?")
    for i, cripto in enumerate(criptos_disponibles, 1):
        print(f"[{i}] {cripto['nombre']} ({cripto['simbolo']}) - {cripto['cantidad']:.8f} disponibles")
    
    try:
        opcion = int(input("\nSelecciona (numero): "))
        if opcion < 1 or opcion > len(criptos_disponibles):
            print("❌ Opción inválida")
            input("\nPresiona Enter...")
            return
        
        cripto_operacion = criptos_disponibles[opcion - 1]
        
    except ValueError:
        print("❌ Opción inválida")
        input("\nPresiona Enter...")
        return
    
    # Análisis de mercado y definición de precio
    print("\n" + "-"*60)
    print("ANALISIS DE MERCADO Y DEFINICION DE PRECIO")
    print("-"*60)
    
    config = queries.obtener_config()
    comision = config['comision_default']
    ganancia_objetivo = config['ganancia_neta_default']
    
    costo_promedio = cripto_operacion['precio_promedio']
    precio_sugerido = calc.calcular_precio_sugerido(costo_promedio, ganancia_objetivo, comision)
    
    print(f"\nUsando {comision}% de comision y un objetivo de {ganancia_objetivo}% de ganancia...")
    print(f"Costo promedio actual: ${costo_promedio:.4f}")
    print(f"Precio sugerido: ${precio_sugerido:.4f}")
    
    while True:
        try:
            precio_str = input("\n¿Que precio vas a publicar en tu anuncio?: ")
            precio_publicado = float(precio_str)
            
            if precio_publicado <= 0:
                print("❌ El precio debe ser mayor a 0")
                continue
            
            # Calcular ganancia neta estimada
            ganancia_neta_estimada = calc.calcular_ganancia_neta_estimada(
                costo_promedio, precio_publicado, comision
            )
            
            print(f"\nGanancia neta estimada: {ganancia_neta_estimada:.2f}%")
            
            if ganancia_neta_estimada < 0:
                print("⚠️  ADVERTENCIA: Este precio resulta en PÉRDIDA")
            elif ganancia_neta_estimada < 0.5:
                print("⚠️  ADVERTENCIA: Ganancia muy baja")
            
            confirmar = input("\n¿Confirmar este precio? (s/n): ").lower()
            if confirmar == 's':
                break
            
        except ValueError:
            print("❌ Precio inválido")
    
    # Actualizar día con precio y cripto
    db.execute_update("""
        UPDATE dias
        SET cripto_operada_id = ?,
            precio_publicado = ?
        WHERE id = ?
    """, (cripto_operacion['id'], precio_publicado, dia_id))
    
    print("✅ Precio de venta definido")
    
    log.precio_definido(
        cripto_operacion['simbolo'],
        costo_promedio,
        comision,
        ganancia_objetivo,
        precio_publicado,
        ganancia_neta_estimada
    )
    
    # Registro de ventas
    print("\n" + "-"*60)
    print("REGISTRO DE VENTAS")
    print("-"*60)
    
    limites = queries.obtener_limites_ventas()
    print(f"\nLímites recomendados: {limites[0]}-{limites[1]} ventas/día")
    print("(Para evitar bloqueos bancarios)")
    
    num_venta = 1
    
    # --- INICIO DEL BUCLE CORREGIDO ---
    while True:
        # Contar ventas registradas
        ventas_actuales = queries.contar_ventas_dia(dia_id)
        
        # ⭐ NUEVA VALIDACIÓN: Verificar si hay capital disponible
        cantidad_disponible = obtener_cantidad_disponible(ciclo['id'], cripto_operacion['id'])
        
        if cantidad_disponible <= 0.00000001:  # Prácticamente 0
            print("\n" + "="*60)
            print("💰 CAPITAL AGOTADO")
            print("="*60)
            print(f"\n✅ Has vendido todo el {cripto_operacion['simbolo']} disponible")
            print(f"   Total de ventas: {ventas_actuales}")
            print("\n🔒 No puedes registrar más ventas")
            print("   Procediendo al cierre del día...")
            input("\nPresiona Enter para continuar...")
            break
        
        # ⭐ ALERTA DE LÍMITE
        if ventas_actuales >= limites[1]:
            print(f"\n🚨 ADVERTENCIA: Has alcanzado el límite recomendado de {limites[1]} ventas")
            print("   Considera cerrar el día para evitar bloqueos bancarios")
            continuar = input("   ¿Registrar otra venta de todos modos? (s/n): ").lower()
            if continuar != 's':
                break
        elif ventas_actuales == limites[1] - 1:
            print(f"\n⚠️  Estás cerca del límite: {ventas_actuales}/{limites[1]} ventas")
        
        print("\n" + "="*60)
        print(f"VENTA #{num_venta}")
        print("="*60)
        print(f"\nDisponible: {cantidad_disponible:.8f} {cripto_operacion['simbolo']}")
        print(f"Precio de venta: ${precio_publicado:.4f}")
        
        try:
            cantidad_str = input(f"\n¿Cuántos {cripto_operacion['simbolo']} vendiste? (0 para terminar): ")
            cantidad_vendida = float(cantidad_str)
            
            if cantidad_vendida == 0:
                print("Finalizando registro de ventas...")
                break
            
            if cantidad_vendida < 0:
                print("❌ La cantidad no puede ser negativa")
                continue
            
            if cantidad_vendida > cantidad_disponible:
                print(f"❌ No hay suficiente {cripto_operacion['simbolo']} disponible")
                continue
            
            # Registrar venta
            venta_id = registrar_venta_manual(
                dia_id,
                cripto_operacion['id'],
                cantidad_vendida,
                precio_publicado,
                comision
            )
            
            print(f"✅ Venta #{num_venta} registrada")
            
            # Preguntar si quiere registrar otra
            otra = input("\n¿Registrar otra venta? (s/n): ").lower()
            if otra != 's':
                break
            
            num_venta += 1
            
        except ValueError:
            print("❌ Cantidad inválida")
        except Exception as e:
            print(f"❌ Error al registrar venta: {e}")
            log.error("Error en registro de venta", str(e))

    # --- FIN DEL BUCLE ---

    # Resumen de ventas
    ventas_totales = queries.contar_ventas_dia(dia_id)
    print(f"\n✅ Total de ventas registradas: {ventas_totales}")
    
    # Cierre del día
    print("\n" + "-"*60)
    print("CIERRE DEL DIA")
    print("-"*60)
    
    cerrar = input("\n¿Deseas cerrar el dia de operacion? (s/n): ").lower()
    
    if cerrar == 's':
        print("\n" + "="*60)
        print("CERRANDO DÍA DE OPERACIÓN")
        print("="*60)
        
        print("\n⚠️  Esta acción no se puede deshacer")
        confirmar_cierre = input("¿Confirmar cierre del día? (s/n): ").lower()
        
        if confirmar_cierre == 's':
            if cerrar_dia_operacion(dia_id):
                # Preguntar por interés compuesto
                print("\n¿Deseas aplicar interés compuesto?")
                print("(Reinvierte las ganancias en el siguiente día)")
                interes = input("Aplicar interés compuesto? (s/n): ").lower()
                
                if interes == 's':
                    aplicar_interes_compuesto(ciclo['id'])
        else:
            print("❌ Cierre cancelado")
    
    input("\nPresiona Enter para volver al menú...")


# ===================================================================
# MENÚ AVANZADO
# ===================================================================

def menu_operador_avanzado():
    """Menú con opciones avanzadas del operador"""
    
    while True:
        print("\n" + "="*60)
        print("MENÚ AVANZADO DEL OPERADOR")
        print("="*60)
        print("[1] Ver día abierto")
        print("[2] Cerrar día manualmente")
        print("[3] Ver historial de días")
        print("[4] Ver ventas de un día")
        print("[5] Aplicar interés compuesto")
        print("[6] Volver")
        print("="*60)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            ver_dia_abierto()
        elif opcion == "2":
            cerrar_dia_manual()
        elif opcion == "3":
            ver_historial_dias()
        elif opcion == "4":
            ver_ventas_dia()
        elif opcion == "5":
            aplicar_interes_manual()
        elif opcion == "6":
            break
        else:
            print("❌ Opción inválida")
            input("\nPresiona Enter...")


def ver_dia_abierto():
    """Muestra información del día abierto"""
    
    ciclo = queries.obtener_ciclo_activo()
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        input("\nPresiona Enter...")
        return
    
    dia = queries.obtener_dia_abierto(ciclo['id'])
    
    if not dia:
        print("\n⚠️  No hay día abierto en el ciclo activo")
        input("\nPresiona Enter...")
        return
    
    print("\n" + "="*60)
    print(f"DÍA #{dia['numero_dia']} - ABIERTO")
    print("="*60)
    
    print(f"\nFecha inicio: {dia['fecha']}")
    print(f"Capital inicial: ${dia['capital_inicial']:.2f}")
    
    if dia['cripto_operada_id']:
        cripto = db.execute_query(
            "SELECT nombre, simbolo FROM criptomonedas WHERE id = ?",
            (dia['cripto_operada_id'],),
            fetch_one=True
        )
        print(f"Cripto operada: {cripto['nombre']} ({cripto['simbolo']})")
        print(f"Precio publicado: ${dia['precio_publicado']:.4f}")
    
    # Ventas del día
    ventas = queries.obtener_ventas_dia(dia['id'])
    num_ventas = len(ventas) if ventas else 0
    
    print(f"\nVentas registradas: {num_ventas}")
    
    if ventas:
        efectivo_acumulado = sum(v['efectivo_recibido'] for v in ventas)
        ganancia_acumulada = sum(v['ganancia_neta'] for v in ventas)
        
        print(f"Efectivo recibido: ${efectivo_acumulado:.2f}")
        print(f"Ganancia acumulada: ${ganancia_acumulada:.2f}")
    
    input("\nPresiona Enter...")


def cerrar_dia_manual():
    """Cierra el día abierto manualmente"""
    
    ciclo = queries.obtener_ciclo_activo()
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        input("\nPresiona Enter...")
        return
    
    dia = queries.obtener_dia_abierto(ciclo['id'])
    
    if not dia:
        print("\n⚠️  No hay día abierto")
        input("\nPresiona Enter...")
        return
    
    print(f"\n¿Cerrar día #{dia['numero_dia']}?")
    confirmar = input("(s/n): ").lower()
    
    if confirmar == 's':
        cerrar_dia_operacion(dia['id'])
    else:
        print("❌ Operación cancelada")
    
    input("\nPresiona Enter...")


def ver_historial_dias():
    """Muestra historial de días del ciclo activo"""
    
    ciclo = queries.obtener_ciclo_activo()
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        input("\nPresiona Enter...")
        return
    
    dias = db.execute_query("""
        SELECT * FROM dias
        WHERE ciclo_id = ?
        ORDER BY numero_dia DESC
    """, (ciclo['id'],))
    
    if not dias:
        print("\n⚠️  No hay días registrados")
        input("\nPresiona Enter...")
        return
    
    print("\n" + "="*60)
    print(f"HISTORIAL DE DÍAS - CICLO #{ciclo['id']}")
    print("="*60)
    
    for dia in dias:
        estado_emoji = "🔵" if dia['estado'] == 'abierto' else "✅"
        print(f"\n{estado_emoji} Día #{dia['numero_dia']} - {dia['estado'].upper()}")
        print(f"   Fecha: {dia['fecha']}")
        print(f"   Capital inicial: ${dia['capital_inicial']:.2f}")
        
        if dia['estado'] == 'cerrado':
            print(f"   Capital final: ${dia['capital_final']:.2f}")
            print(f"   Ganancia neta: ${dia['ganancia_neta']:.2f}")
            
            num_ventas = queries.contar_ventas_dia(dia['id'])
            print(f"   Ventas: {num_ventas}")
    
    input("\nPresiona Enter...")


def ver_ventas_dia():
    """Muestra ventas de un día específico"""
    
    try:
        dia_id = int(input("\nID del día: "))
        
        ventas = queries.obtener_ventas_dia(dia_id)
        
        if not ventas:
            print("\n⚠️  No hay ventas en este día")
            input("\nPresiona Enter...")
            return
        
        print("\n" + "="*60)
        print(f"VENTAS DEL DÍA #{dia_id}")
        print("="*60)
        
        total_efectivo = 0
        total_ganancia = 0
        
        for i, venta in enumerate(ventas, 1):
            cripto = db.execute_query(
                "SELECT simbolo FROM criptomonedas WHERE id = ?",
                (venta['cripto_id'],),
                fetch_one=True
            )
            
            print(f"\nVenta #{i}")
            print(f"  Cantidad: {venta['cantidad']:.8f} {cripto['simbolo']}")
            print(f"  Precio: ${venta['precio_unitario']:.4f}")
            print(f"  Total: ${venta['monto_venta']:.2f}")
            print(f"  Comisión: ${venta['comision']:.2f}")
            print(f"  Efectivo recibido: ${venta['efectivo_recibido']:.2f}")
            print(f"  Ganancia neta: ${venta['ganancia_neta']:.2f}")
            
            total_efectivo += venta['efectivo_recibido']
            total_ganancia += venta['ganancia_neta']
        
        print("\n" + "-"*60)
        print(f"TOTALES:")
        print(f"  Efectivo total: ${total_efectivo:.2f}")
        print(f"  Ganancia total: ${total_ganancia:.2f}")
        
    except ValueError:
        print("❌ ID inválido")
    
    input("\nPresiona Enter...")


def aplicar_interes_manual():
    """Aplica interés compuesto manualmente"""
    
    ciclo = queries.obtener_ciclo_activo()
    if not ciclo:
        print("\n❌ No hay ciclo activo")
        input("\nPresiona Enter...")
        return
    
    aplicar_interes_compuesto(ciclo['id'])
    
    input("\nPresiona Enter...")


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    modulo_operador()