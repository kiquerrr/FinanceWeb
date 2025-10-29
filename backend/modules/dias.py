# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE DÍAS - Gestión de días de operación (CORREGIDO)
=============================================================================
Integrado con logger.py y calculos.py para precisión total
✅ Ahora usa db_manager para conexiones seguras
"""

from datetime import datetime, timedelta
from core.logger import log
from core.calculos import calc
from core.db_manager import db


# ===================================================================
# FUNCIONES DE OBTENCIÓN DE DATOS
# ===================================================================

def obtener_cripto_por_id(cripto_id):
    """Obtiene información de una criptomoneda"""
    return db.execute_query("""
        SELECT id, nombre, simbolo, tipo
        FROM criptomonedas
        WHERE id = ?
    """, (cripto_id,), fetch_one=True)


def obtener_costo_promedio(cripto_id, ciclo_id):
    """Obtiene el costo promedio de una cripto en un ciclo"""
    resultado = db.execute_query("""
        SELECT precio_promedio
        FROM boveda_ciclo
        WHERE cripto_id = ? AND ciclo_id = ?
    """, (cripto_id, ciclo_id), fetch_one=True)
    
    return resultado['precio_promedio'] if resultado else 0


def obtener_cantidad_disponible(cripto_id, ciclo_id):
    """Obtiene la cantidad disponible de una cripto"""
    resultado = db.execute_query("""
        SELECT cantidad
        FROM boveda_ciclo
        WHERE cripto_id = ? AND ciclo_id = ?
    """, (cripto_id, ciclo_id), fetch_one=True)
    
    return resultado['cantidad'] if resultado else 0


def obtener_criptos_disponibles(ciclo_id):
    """Obtiene todas las criptos con cantidad > 0 en un ciclo"""
    return db.execute_query("""
        SELECT 
            c.id,
            c.nombre,
            c.simbolo,
            bc.cantidad,
            bc.precio_promedio,
            (bc.cantidad * bc.precio_promedio) as valor_usd
        FROM boveda_ciclo bc
        JOIN criptomonedas c ON bc.cripto_id = c.id
        WHERE bc.ciclo_id = ? AND bc.cantidad > 0
        ORDER BY c.nombre
    """, (ciclo_id,))


def calcular_capital_actual_criptos(ciclo_id):
    """Calcula el valor total de las criptos disponibles"""
    criptos = obtener_criptos_disponibles(ciclo_id)
    
    criptos_info = [
        (c['nombre'], c['cantidad'], c['precio_promedio'])
        for c in criptos
    ]
    
    return calc.calcular_capital_total(criptos_info)


def obtener_dia(dia_id):
    """Obtiene información de un día"""
    return db.execute_query(
        "SELECT * FROM dias WHERE id = ?",
        (dia_id,),
        fetch_one=True
    )


def obtener_dia_actual(ciclo_id):
    """Obtiene el día actual activo del ciclo"""
    return db.execute_query("""
        SELECT * FROM dias
        WHERE ciclo_id = ? AND estado = 'abierto'
        ORDER BY numero_dia DESC
        LIMIT 1
    """, (ciclo_id,), fetch_one=True)


def obtener_ventas_del_dia(dia_id):
    """Obtiene todas las ventas de un día"""
    return db.execute_query("""
        SELECT 
            v.*,
            c.nombre as cripto_nombre,
            c.simbolo as cripto_simbolo
        FROM ventas v
        JOIN criptomonedas c ON v.cripto_id = c.id
        WHERE v.dia_id = ?
        ORDER BY v.fecha
    """, (dia_id,))


def contar_ventas_del_dia(dia_id):
    """Cuenta cuántas ventas se han hecho en el día"""
    resultado = db.execute_query(
        "SELECT COUNT(*) as total FROM ventas WHERE dia_id = ?",
        (dia_id,),
        fetch_one=True
    )
    return resultado['total']


def obtener_resumen_dias(ciclo_id):
    """Obtiene resumen de todos los días de un ciclo"""
    return db.execute_query("""
        SELECT 
            numero_dia,
            fecha,
            capital_inicial,
            capital_final,
            ganancia_neta,
            estado
        FROM dias
        WHERE ciclo_id = ?
        ORDER BY numero_dia
    """, (ciclo_id,))


# ===================================================================
# INICIAR DÍA
# ===================================================================

def iniciar_dia(ciclo_id):
    """Inicia un nuevo día de operación"""
    
    # Verificar si ya hay un día abierto
    dia_actual = obtener_dia_actual(ciclo_id)
    if dia_actual:
        log.advertencia(
            f"Ya existe un día abierto (#{dia_actual['numero_dia']}) en el ciclo #{ciclo_id}",
            categoria='operaciones'
        )
        return dia_actual['id']
    
    # Calcular número de día
    resultado = db.execute_query("""
        SELECT COALESCE(MAX(numero_dia), 0) + 1 as siguiente_dia
        FROM dias
        WHERE ciclo_id = ?
    """, (ciclo_id,), fetch_one=True)
    numero_dia = resultado['siguiente_dia']
    
    # Calcular capital inicial del día
    capital_inicial = calcular_capital_actual_criptos(ciclo_id)
    
    # Obtener criptos disponibles para log
    criptos_disponibles = obtener_criptos_disponibles(ciclo_id)
    criptos_info = [
        (c['nombre'], c['cantidad'], c['valor_usd']) 
        for c in criptos_disponibles
    ]
    
    # Insertar día en BD
    dia_id = db.execute_update("""
        INSERT INTO dias (
            ciclo_id, numero_dia, capital_inicial, 
            estado, fecha
        ) VALUES (?, ?, ?, 'abierto', datetime('now'))
    """, (ciclo_id, numero_dia, capital_inicial))
    
    # REGISTRAR EN LOG
    log.dia_iniciado(
        ciclo_id=ciclo_id,
        dia_num=numero_dia,
        capital_inicial=capital_inicial,
        criptos_disponibles=criptos_info
    )
    
    print(f"✅ Día #{numero_dia} iniciado con ${capital_inicial:.2f}")
    
    return dia_id


# ===================================================================
# DEFINIR PRECIO DE VENTA
# ===================================================================

def definir_precio_venta(dia_id, cripto_id, precio_publicado):
    """Registra el precio de venta para el día"""
    
    # Obtener día y ciclo
    dia = obtener_dia(dia_id)
    ciclo_id = dia['ciclo_id']
    
    # Obtener info de la cripto
    cripto = obtener_cripto_por_id(cripto_id)
    costo_promedio = obtener_costo_promedio(cripto_id, ciclo_id)
    
    # Obtener configuración
    config = db.execute_query(
        "SELECT comision_default, ganancia_neta_default FROM config WHERE id = 1",
        fetch_one=True
    )
    comision = config['comision_default']
    ganancia_objetivo = config['ganancia_neta_default']
    
    # Calcular ganancia neta estimada con el precio publicado
    ganancia_neta_estimada = calc.calcular_ganancia_neta_estimada(
        costo_promedio=costo_promedio,
        precio_venta=precio_publicado
    )
    
    # Actualizar día con la info
    db.execute_update("""
        UPDATE dias SET
            cripto_operada_id = ?,
            precio_publicado = ?
        WHERE id = ?
    """, (cripto_id, precio_publicado, dia_id))
    
    # REGISTRAR EN LOG
    log.precio_definido(
        cripto=cripto['nombre'],
        costo_promedio=costo_promedio,
        comision=comision,
        ganancia_objetivo=ganancia_objetivo,
        precio_publicado=precio_publicado,
        ganancia_neta_estimada=ganancia_neta_estimada
    )
    
    return True


# ===================================================================
# REGISTRAR VENTA
# ===================================================================

def registrar_venta(dia_id, cripto_id, cantidad, precio_unitario):
    """
    Registra una venta individual
    
    Args:
        dia_id: ID del día
        cripto_id: ID de la criptomoneda
        cantidad: Cantidad vendida
        precio_unitario: Precio de venta por unidad
    
    Returns:
        bool: True si se registró correctamente
    """
    
    # Obtener día
    dia = obtener_dia(dia_id)
    if not dia:
        log.error("Día no encontrado", f"dia_id={dia_id}")
        return False
    
    ciclo_id = dia['ciclo_id']
    
    # Obtener cripto
    cripto = obtener_cripto_por_id(cripto_id)
    if not cripto:
        log.error("Cripto no encontrada", f"cripto_id={cripto_id}")
        return False
    
    # Obtener costo promedio
    costo_unitario = obtener_costo_promedio(cripto_id, ciclo_id)
    
    if costo_unitario == 0:
        log.error("Costo promedio es 0", f"cripto_id={cripto_id}")
        return False
    
    # Verificar cantidad disponible
    cantidad_disponible = obtener_cantidad_disponible(cripto_id, ciclo_id)
    
    if cantidad > cantidad_disponible:
        log.error(
            "Cantidad insuficiente",
            f"Solicitado: {cantidad}, Disponible: {cantidad_disponible}"
        )
        return False
    
    # Obtener comisión
    config = db.execute_query(
        "SELECT comision_default FROM config WHERE id = 1",
        fetch_one=True
    )
    comision_pct = config['comision_default']
    
    # Calcular valores de la venta
    resultado_venta = calc.calcular_venta(
        cantidad=cantidad,
        costo_unitario=costo_unitario,
        precio_venta=precio_unitario
    )
    
    if not resultado_venta:
        log.error("Error al calcular venta")
        return False
    
    # Usar transacción para garantizar consistencia
    try:
        with db.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. Insertar venta
            cursor.execute("""
                INSERT INTO ventas (
                    dia_id, cripto_id, cantidad, precio_unitario,
                    costo_total, monto_venta, comision, efectivo_recibido,
                    ganancia_bruta, ganancia_neta, fecha
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                dia_id,
                cripto_id,
                cantidad,
                precio_unitario,
                resultado_venta['costo_total'],
                resultado_venta['monto_venta'],
                resultado_venta['comision'],
                resultado_venta['efectivo_recibido'],
                resultado_venta['ganancia_bruta'],
                resultado_venta['ganancia_neta']
            ))
            
            # 2. Actualizar bóveda (restar cantidad vendida)
            cursor.execute("""
                UPDATE boveda_ciclo
                SET cantidad = cantidad - ?
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (cantidad, ciclo_id, cripto_id))
            
            # 3. Registrar efectivo recibido
            cursor.execute("""
                INSERT INTO efectivo_banco (ciclo_id, dia_id, monto, concepto, fecha)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (
                ciclo_id,
                dia_id,
                resultado_venta['efectivo_recibido'],
                f"Venta de {cantidad:.8f} {cripto['simbolo']}"
            ))
            
            # Commit automático al salir del context manager
        
        # Contar número de venta
        num_venta = contar_ventas_del_dia(dia_id)
        
        # REGISTRAR EN LOG
        log.venta_registrada(
            venta_num=num_venta,
            cripto=cripto['nombre'],
            cantidad_vendida=cantidad,
            precio_unitario=precio_unitario,
            monto_total=resultado_venta['efectivo_recibido'],
            comision_pagada=resultado_venta['comision'],
            ganancia_neta=resultado_venta['ganancia_neta']
        )
        
        return True
        
    except Exception as e:
        log.error("Error al registrar venta", str(e))
        return False


# ===================================================================
# CERRAR DÍA
# ===================================================================

def cerrar_dia(dia_id, ciclo_id):
    """
    Cierra un día de operación y calcula el resultado final
    
    Args:
        dia_id: ID del día a cerrar
        ciclo_id: ID del ciclo
    
    Returns:
        bool: True si se cerró correctamente
    """
    
    # Obtener día
    dia = obtener_dia(dia_id)
    if not dia:
        log.error("Día no encontrado", f"dia_id={dia_id}")
        return False
    
    if dia['estado'] != 'abierto':
        log.advertencia(f"El día #{dia['numero_dia']} ya está {dia['estado']}")
        return False
    
    # Obtener ventas del día
    ventas = obtener_ventas_del_dia(dia_id)
    
    if not ventas or len(ventas) == 0:
        print("\n⚠️  No hay ventas registradas en este día")
        print("    ¿Deseas cerrar el día sin ventas?")
        confirmar = input("    (s/n): ").lower()
        if confirmar != 's':
            print("❌ Cierre cancelado")
            return False
    
    # Calcular capital final en criptos
    capital_final_criptos = calcular_capital_actual_criptos(ciclo_id)
    
    # Obtener efectivo recibido del día
    efectivo_recibido = db.execute_query("""
        SELECT COALESCE(SUM(monto), 0) as total
        FROM efectivo_banco
        WHERE dia_id = ?
    """, (dia_id,), fetch_one=True)['total']
    
    # Capital final total
    capital_final_total = capital_final_criptos + efectivo_recibido
    
    # Calcular totales del día
    totales = db.execute_query("""
        SELECT 
            COALESCE(SUM(monto_venta), 0) as monto_total,
            COALESCE(SUM(comision), 0) as comisiones_total,
            COALESCE(SUM(ganancia_bruta), 0) as ganancia_bruta_total,
            COALESCE(SUM(ganancia_neta), 0) as ganancia_neta_total
        FROM ventas
        WHERE dia_id = ?
    """, (dia_id,), fetch_one=True)
    
    # Actualizar día
    db.execute_update("""
        UPDATE dias SET
            capital_final = ?,
            efectivo_recibido = ?,
            comisiones_pagadas = ?,
            ganancia_bruta = ?,
            ganancia_neta = ?,
            estado = 'cerrado',
            fecha_cierre = datetime('now')
        WHERE id = ?
    """, (
        capital_final_total,
        efectivo_recibido,
        totales['comisiones_total'],
        totales['ganancia_bruta_total'],
        totales['ganancia_neta_total'],
        dia_id
    ))
    
    # Actualizar contador de días operados en el ciclo
    db.execute_update("""
        UPDATE ciclos
        SET dias_operados = dias_operados + 1,
            ganancia_total = ganancia_total + ?
        WHERE id = ?
    """, (totales['ganancia_neta_total'], ciclo_id))
    
    # REGISTRAR EN LOG
    log.dia_cerrado(
        ciclo_id=ciclo_id,
        dia_num=dia['numero_dia'],
        capital_inicial=dia['capital_inicial'],
        capital_final=capital_final_total,
        ganancia_dia=totales['ganancia_neta_total'],
        ventas_realizadas=len(ventas)
    )
    
    # Mostrar resumen
    print("\n" + "="*60)
    print(f"DÍA #{dia['numero_dia']} CERRADO")
    print("="*60)
    print(f"\nCapital inicial: ${dia['capital_inicial']:.2f}")
    print(f"Capital final: ${capital_final_total:.2f}")
    print(f"Efectivo recibido: ${efectivo_recibido:.2f}")
    print(f"Comisiones pagadas: ${totales['comisiones_total']:.2f}")
    print(f"Ganancia bruta: ${totales['ganancia_bruta_total']:.2f}")
    print(f"Ganancia neta: ${totales['ganancia_neta_total']:.2f}")
    print(f"Ventas realizadas: {len(ventas)}")
    print("="*60)
    
    return True


# ===================================================================
# INTERÉS COMPUESTO
# ===================================================================

def aplicar_interes_compuesto(dia_id, ciclo_id):
    """
    Aplica interés compuesto: reinvierte las ganancias del día
    
    Args:
        dia_id: ID del día cerrado
        ciclo_id: ID del ciclo
    
    Returns:
        bool: True si se aplicó correctamente
    """
    
    # Obtener día
    dia = obtener_dia(dia_id)
    if not dia or dia['estado'] != 'cerrado':
        print("❌ Solo se puede aplicar a días cerrados")
        return False
    
    # Obtener efectivo del día
    efectivo = dia['efectivo_recibido']
    
    if efectivo <= 0:
        print("⚠️  No hay efectivo para reinvertir")
        return False
    
    print(f"\nEfectivo disponible para reinvertir: ${efectivo:.2f}")
    print("\n¿En qué cripto deseas reinvertir?")
    
    # Listar criptos disponibles
    criptos = db.execute_query("""
        SELECT id, nombre, simbolo
        FROM criptomonedas
        ORDER BY nombre
    """)
    
    for i, cripto in enumerate(criptos, 1):
        print(f"[{i}] {cripto['nombre']} ({cripto['simbolo']})")
    
    try:
        seleccion = int(input("\nSelecciona (número): ")) - 1
        
        if seleccion < 0 or seleccion >= len(criptos):
            print("❌ Selección inválida")
            return False
        
        cripto = criptos[seleccion]
        
        # Pedir tasa de compra
        tasa = float(input(f"\nTasa de compra (1 {cripto['simbolo']} = $): "))
        
        if tasa <= 0:
            print("❌ Tasa inválida")
            return False
        
        # Calcular cantidad a comprar
        cantidad = efectivo / tasa
        
        print(f"\nSe reinvertirán ${efectivo:.2f} en {cantidad:.8f} {cripto['simbolo']}")
        confirmar = input("¿Confirmar? (s/n): ").lower()
        
        if confirmar != 's':
            print("❌ Reinversión cancelada")
            return False
        
        # Registrar compra
        with db.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. Registrar compra
            cursor.execute("""
                INSERT INTO compras (ciclo_id, cripto_id, cantidad, monto_usd, tasa, fecha)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (ciclo_id, cripto['id'], cantidad, efectivo, tasa))
            
            # 2. Actualizar bóveda
            cursor.execute("""
                SELECT cantidad, precio_promedio
                FROM boveda_ciclo
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (ciclo_id, cripto['id']))
            
            boveda = cursor.fetchone()
            
            if boveda:
                # Calcular nuevo promedio ponderado
                cant_anterior = boveda['cantidad']
                precio_anterior = boveda['precio_promedio']
                
                costo_anterior = cant_anterior * precio_anterior
                costo_nuevo = cantidad * tasa
                
                cantidad_total = cant_anterior + cantidad
                precio_promedio_nuevo = (costo_anterior + costo_nuevo) / cantidad_total
                
                cursor.execute("""
                    UPDATE boveda_ciclo
                    SET cantidad = ?, precio_promedio = ?
                    WHERE ciclo_id = ? AND cripto_id = ?
                """, (cantidad_total, precio_promedio_nuevo, ciclo_id, cripto['id']))
            else:
                # Insertar nuevo
                cursor.execute("""
                    INSERT INTO boveda_ciclo (ciclo_id, cripto_id, cantidad, precio_promedio)
                    VALUES (?, ?, ?, ?)
                """, (ciclo_id, cripto['id'], cantidad, tasa))
            
            # 3. Marcar efectivo como reinvertido
            cursor.execute("""
                UPDATE efectivo_banco
                SET concepto = concepto || ' (Reinvertido)'
                WHERE dia_id = ?
            """, (dia_id,))
        
        log.info(
            f"Interés compuesto aplicado: ${efectivo:.2f} → {cantidad:.8f} {cripto['simbolo']}",
            categoria='operaciones'
        )
        
        print(f"\n✅ Interés compuesto aplicado exitosamente")
        print(f"    ${efectivo:.2f} reinvertidos en {cantidad:.8f} {cripto['simbolo']}")
        
        return True
        
    except ValueError:
        print("❌ Entrada inválida")
        return False
    except Exception as e:
        log.error("Error al aplicar interés compuesto", str(e))
        print(f"❌ Error: {e}")
        return False


# ===================================================================
# VALIDACIONES
# ===================================================================

def validar_limite_ventas(dia_id):
    """
    Valida si se ha alcanzado el límite de ventas
    
    Args:
        dia_id: ID del día
    
    Returns:
        bool: True si puede seguir vendiendo
    """
    
    num_ventas = contar_ventas_del_dia(dia_id)
    
    limites = db.execute_query(
        "SELECT limite_ventas_min, limite_ventas_max FROM config WHERE id = 1",
        fetch_one=True
    )
    
    if num_ventas >= limites['limite_ventas_max']:
        return False
    
    return True


# ===================================================================
# MOSTRAR PROGRESO
# ===================================================================

def mostrar_progreso_ciclo(ciclo_id):
    """Muestra el progreso del ciclo con todos sus días"""
    
    from ciclos import obtener_ciclo
    
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        print("❌ Ciclo no encontrado")
        return
    
    print("\n" + "="*60)
    print(f"PROGRESO DEL CICLO #{ciclo_id}")
    print("="*60)
    
    print(f"\nEstado: {ciclo['estado'].upper()}")
    print(f"Inversión inicial: ${ciclo['inversion_inicial']:.2f}")
    print(f"Días planificados: {ciclo['dias_planificados']}")
    print(f"Días operados: {ciclo['dias_operados']}")
    
    # Obtener días
    dias = obtener_resumen_dias(ciclo_id)
    
    if not dias:
        print("\n⚠️  No hay días registrados en este ciclo")
        return
    
    print(f"\n{'='*60}")
    print("DÍAS OPERADOS:")
    print(f"{'='*60}")
    
    ganancia_acumulada = 0
    
    for dia in dias:
        estado_emoji = "✅" if dia['estado'] == 'cerrado' else "🔄"
        
        print(f"\n{estado_emoji} Día #{dia['numero_dia']} - {dia['fecha']}")
        print(f"    Capital inicial: ${dia['capital_inicial']:.2f}")
        
        if dia['estado'] == 'cerrado':
            print(f"    Capital final: ${dia['capital_final']:.2f}")
            print(f"    Ganancia: ${dia['ganancia_neta']:.2f}")
            ganancia_acumulada += dia['ganancia_neta']
        else:
            print(f"    Estado: ABIERTO")
    
    print(f"\n{'='*60}")
    print(f"Ganancia acumulada: ${ganancia_acumulada:.2f}")
    
    if ciclo['inversion_inicial'] > 0:
        roi = (ganancia_acumulada / ciclo['inversion_inicial']) * 100
        print(f"ROI actual: {roi:.2f}%")
    
    print("="*60)


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    print("Módulo Días - Versión 2.0 (Corregido)")
    print("\nEste módulo debe ejecutarse desde el sistema principal")
