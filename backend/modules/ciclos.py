# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE CICLOS - Gestión de Ciclos Globales (CORREGIDO)
=============================================================================
Maneja el ciclo de vida completo de los ciclos de arbitraje
✅ Ahora usa db_manager para conexiones seguras
"""

from datetime import datetime, timedelta
from core.logger import log
from core.calculos import calc
from core.db_manager import db


# ===================================================================
# CREAR CICLO
# ===================================================================

def crear_ciclo(dias_duracion=15):
    """
    Crea un nuevo ciclo global
    
    Args:
        dias_duracion: Duración planificada del ciclo en días
    
    Returns:
        int: ID del ciclo creado
    """
    
    fecha_inicio = datetime.now().date()
    fecha_fin = fecha_inicio + timedelta(days=dias_duracion)
    
    # Calcular inversión inicial correctamente
    inversion_inicial = db.execute_query(
        """SELECT COALESCE(SUM(bc.cantidad * bc.precio_promedio), 0) as capital_inicial
           FROM boveda_ciclo bc
           WHERE bc.cantidad > 0""",
        fetch_one=True
    )['capital_inicial']
    
    # Si no hay capital, advertir
    if inversion_inicial == 0:
        print("\n⚠️  ADVERTENCIA: No hay capital en la bóveda")
        print("    La inversión inicial será $0.00")
        print("    Fondea la bóveda antes de operar")
        
        continuar = input("\n¿Continuar creando el ciclo? (s/n): ").lower()
        if continuar != 's':
            print("❌ Creación de ciclo cancelada")
            return None
    
    # Insertar ciclo
    ciclo_id = db.execute_update("""
        INSERT INTO ciclos (
            fecha_inicio, 
            fecha_fin_estimada, 
            dias_planificados,
            inversion_inicial,
            estado
        ) VALUES (?, ?, ?, ?, 'activo')
    """, (
        fecha_inicio.strftime('%Y-%m-%d'),
        fecha_fin.strftime('%Y-%m-%d'),
        dias_duracion,
        inversion_inicial
    ))
    
    # Registrar en log
    log.ciclo_creado(
        ciclo_id=ciclo_id,
        dias=dias_duracion,
        capital_inicial=inversion_inicial,
        fecha_inicio=fecha_inicio.strftime('%Y-%m-%d'),
        fecha_fin=fecha_fin.strftime('%Y-%m-%d')
    )
    
    print(f"\n✅ Nuevo ciclo #{ciclo_id} creado exitosamente!")
    print(f"    Duración: {dias_duracion} días")
    print(f"    Fecha inicio: {fecha_inicio}")
    print(f"    Fecha fin estimada: {fecha_fin}")
    print(f"    Inversión inicial: ${inversion_inicial:.2f}")
    
    return ciclo_id


# ===================================================================
# OBTENER INFORMACIÓN DE CICLOS
# ===================================================================

def obtener_ciclo_activo():
    """Obtiene el ciclo actualmente activo"""
    return db.execute_query("""
        SELECT * FROM ciclos
        WHERE estado = 'activo'
        ORDER BY id DESC
        LIMIT 1
    """, fetch_one=True)


def obtener_ciclo(ciclo_id):
    """Obtiene información de un ciclo específico"""
    return db.execute_query(
        "SELECT * FROM ciclos WHERE id = ?",
        (ciclo_id,),
        fetch_one=True
    )


def calcular_dias_transcurridos(ciclo_id):
    """Calcula cuántos días han transcurrido desde el inicio del ciclo"""
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        return 0
    
    fecha_inicio = datetime.strptime(ciclo['fecha_inicio'], '%Y-%m-%d').date()
    dias_transcurridos = (datetime.now().date() - fecha_inicio).days
    
    return dias_transcurridos


def calcular_dias_restantes(ciclo_id):
    """Calcula cuántos días faltan para completar el ciclo"""
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        return 0
    
    dias_transcurridos = calcular_dias_transcurridos(ciclo_id)
    dias_restantes = max(0, ciclo['dias_planificados'] - dias_transcurridos)
    
    return dias_restantes


def verificar_ciclo_completado(ciclo_id):
    """
    Verifica si el ciclo ha alcanzado su duración planificada
    
    Returns:
        tuple: (completado: bool, mensaje: str)
    """
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        return False, "Ciclo no encontrado"
    
    dias_transcurridos = calcular_dias_transcurridos(ciclo_id)
    dias_planificados = ciclo['dias_planificados']
    
    if dias_transcurridos >= dias_planificados:
        return True, f"El ciclo ha completado sus {dias_planificados} días planificados"
    
    return False, f"Quedan {dias_planificados - dias_transcurridos} días para completar el ciclo"


# ===================================================================
# VALIDACIONES DE CICLO
# ===================================================================

def puede_operar_dia(ciclo_id):
    """
    Verifica si se puede operar un nuevo día en el ciclo
    
    Returns:
        tuple: (puede_operar: bool, mensaje: str, accion_sugerida: str)
    """
    
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        return False, "Ciclo no encontrado", None
    
    if ciclo['estado'] != 'activo':
        return False, f"El ciclo está {ciclo['estado']}", None
    
    # Verificar si el ciclo ha completado su duración
    completado, mensaje = verificar_ciclo_completado(ciclo_id)
    
    if completado:
        return False, mensaje, "CERRAR_O_EXTENDER"
    
    # Verificar si hay un día abierto
    dia_abierto = db.execute_query("""
        SELECT * FROM dias
        WHERE ciclo_id = ? AND estado = 'abierto'
    """, (ciclo_id,), fetch_one=True)
    
    if dia_abierto:
        return False, f"Ya hay un día abierto (#{dia_abierto['numero_dia']})", "CERRAR_DIA"
    
    return True, "Puede operar", None


# ===================================================================
# GESTIÓN DEL CICLO
# ===================================================================

def gestionar_ciclo_activo():
    """
    Gestiona el ciclo activo: lo obtiene o crea uno nuevo
    
    Returns:
        int: ID del ciclo activo
    """
    
    ciclo = obtener_ciclo_activo()
    
    if ciclo:
        print(f"\n📊 Ciclo activo: #{ciclo['id']}")
        mostrar_info_ciclo(ciclo['id'])
        return ciclo['id']
    else:
        print("\n⚠️  No hay ciclo activo")
        print("\nPara operar necesitas crear un ciclo global")
        
        crear = input("\n¿Deseas crear un nuevo ciclo? (s/n): ").lower()
        
        if crear == 's':
            try:
                dias = int(input("¿Cuántos días durará el ciclo? (15): ") or "15")
                
                if dias < 1 or dias > 365:
                    print("❌ Duración inválida (debe ser entre 1 y 365 días)")
                    return None
                
                ciclo_id = crear_ciclo(dias)
                return ciclo_id
                
            except ValueError:
                print("❌ Valor inválido")
                return None
        else:
            return None


def mostrar_info_ciclo(ciclo_id):
    """Muestra información detallada del ciclo"""
    
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        print("❌ Ciclo no encontrado")
        return
    
    dias_transcurridos = calcular_dias_transcurridos(ciclo_id)
    dias_restantes = calcular_dias_restantes(ciclo_id)
    
    print(f"    Estado: {ciclo['estado'].upper()}")
    print(f"    Duración: {ciclo['dias_planificados']} días")
    print(f"    Transcurridos: {dias_transcurridos} días")
    print(f"    Restantes: {dias_restantes} días")
    print(f"    Inversión inicial: ${ciclo['inversion_inicial']:.2f}")
    print(f"    Días operados: {ciclo['dias_operados']}")
    
    if ciclo['ganancia_total']:
        roi = (ciclo['ganancia_total'] / ciclo['inversion_inicial'] * 100) if ciclo['inversion_inicial'] > 0 else 0
        print(f"    Ganancia acumulada: ${ciclo['ganancia_total']:.2f}")
        print(f"    ROI: {roi:.2f}%")


# ===================================================================
# CERRAR Y EXTENDER CICLO
# ===================================================================

def cerrar_ciclo(ciclo_id):
    """Cierra un ciclo y calcula estadísticas finales"""
    
    print("\n" + "="*60)
    print("CERRANDO CICLO")
    print("="*60)
    
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        print("❌ Ciclo no encontrado")
        return False
    
    # Verificar que no haya días abiertos
    dia_abierto = db.execute_query("""
        SELECT * FROM dias
        WHERE ciclo_id = ? AND estado = 'abierto'
    """, (ciclo_id,), fetch_one=True)
    
    if dia_abierto:
        print(f"❌ No se puede cerrar el ciclo")
        print(f"    Hay un día abierto (#{dia_abierto['numero_dia']})")
        print("    Cierra el día primero")
        return False
    
    # Calcular estadísticas finales
    with db.get_cursor(commit=False) as cursor:
        # Días operados
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM dias WHERE ciclo_id = ? AND estado = 'cerrado'
        """, (ciclo_id,))
        dias_operados = cursor.fetchone()['total']
        
        # Ganancia total
        cursor.execute("""
            SELECT COALESCE(SUM(ganancia_neta), 0) as total
            FROM dias WHERE ciclo_id = ? AND estado = 'cerrado'
        """, (ciclo_id,))
        ganancia_total = cursor.fetchone()['total']
        
        # Capital final (criptos en bóveda)
        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_promedio), 0) as capital
            FROM boveda_ciclo
            WHERE ciclo_id = ?
        """, (ciclo_id,))
        capital_final = cursor.fetchone()['capital']
    
    # Mostrar resumen
    print(f"\nRESUMEN DEL CICLO #{ciclo_id}:")
    print(f"  Días operados: {dias_operados} / {ciclo['dias_planificados']}")
    print(f"  Inversión inicial: ${ciclo['inversion_inicial']:.2f}")
    print(f"  Ganancia total: ${ganancia_total:.2f}")
    print(f"  Capital final: ${capital_final:.2f}")
    
    roi = (ganancia_total / ciclo['inversion_inicial'] * 100) if ciclo['inversion_inicial'] > 0 else 0
    print(f"  ROI: {roi:.2f}%")
    
    # Confirmar cierre
    print("\n⚠️  Esta acción es irreversible")
    confirmar = input("\n¿Confirmar cierre del ciclo? (escribe 'CERRAR'): ").strip()
    
    if confirmar != "CERRAR":
        print("❌ Cierre cancelado")
        return False
    
    # Actualizar ciclo en BD
    db.execute_update("""
        UPDATE ciclos SET
            estado = 'cerrado',
            fecha_cierre = datetime('now'),
            dias_operados = ?,
            ganancia_total = ?,
            capital_final = ?,
            roi_total = ?
        WHERE id = ?
    """, (dias_operados, ganancia_total, capital_final, roi, ciclo_id))
    
    # Registrar en log
    log.ciclo_cerrado(
        ciclo_id=ciclo_id,
        dias_operados=dias_operados,
        inversion_inicial=ciclo['inversion_inicial'],
        ganancia_total=ganancia_total,
        capital_final=capital_final
    )
    
    print(f"\n✅ Ciclo #{ciclo_id} cerrado exitosamente")
    return True


def extender_ciclo(ciclo_id, dias_adicionales):
    """Extiende la duración de un ciclo"""
    
    if dias_adicionales < 1:
        print("❌ Días adicionales debe ser mayor a 0")
        return False
    
    ciclo = obtener_ciclo(ciclo_id)
    if not ciclo:
        print("❌ Ciclo no encontrado")
        return False
    
    nueva_duracion = ciclo['dias_planificados'] + dias_adicionales
    fecha_inicio = datetime.strptime(ciclo['fecha_inicio'], '%Y-%m-%d').date()
    nueva_fecha_fin = fecha_inicio + timedelta(days=nueva_duracion)
    
    # Actualizar ciclo
    db.execute_update("""
        UPDATE ciclos SET
            dias_planificados = ?,
            fecha_fin_estimada = ?
        WHERE id = ?
    """, (nueva_duracion, nueva_fecha_fin.strftime('%Y-%m-%d'), ciclo_id))
    
    log.info(
        f"Ciclo #{ciclo_id} extendido: +{dias_adicionales} días. Nueva duración: {nueva_duracion} días",
        categoria='ciclos'
    )
    
    print(f"\n✅ Ciclo extendido exitosamente")
    print(f"    Duración anterior: {ciclo['dias_planificados']} días")
    print(f"    Nueva duración: {nueva_duracion} días")
    print(f"    Nueva fecha fin: {nueva_fecha_fin}")
    
    return True


# ===================================================================
# ESTADÍSTICAS
# ===================================================================

def mostrar_estadisticas_completas():
    """Muestra estadísticas completas de todos los ciclos"""
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DE CICLOS")
    print("="*60)
    
    with db.get_cursor(commit=False) as cursor:
        # Total de ciclos
        cursor.execute("SELECT COUNT(*) as total FROM ciclos")
        total_ciclos = cursor.fetchone()['total']
        
        # Ciclos cerrados
        cursor.execute("SELECT COUNT(*) as total FROM ciclos WHERE estado = 'cerrado'")
        ciclos_cerrados = cursor.fetchone()['total']
        
        # Ciclo activo
        cursor.execute("SELECT * FROM ciclos WHERE estado = 'activo' ORDER BY id DESC LIMIT 1")
        ciclo_activo = cursor.fetchone()
        
        print(f"\n📊 GENERAL:")
        print(f"    Total de ciclos: {total_ciclos}")
        print(f"    Ciclos cerrados: {ciclos_cerrados}")
        print(f"    Ciclos activos: {1 if ciclo_activo else 0}")
        
        if ciclo_activo:
            print(f"\n🔄 CICLO ACTIVO (#{ciclo_activo['id']}):")
            mostrar_info_ciclo(ciclo_activo['id'])
        
        if ciclos_cerrados > 0:
            # Estadísticas de ciclos cerrados
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(dias_operados) as dias_promedio,
                    SUM(ganancia_total) as ganancia_total,
                    AVG(roi_total) as roi_promedio
                FROM ciclos
                WHERE estado = 'cerrado'
            """)
            
            stats = cursor.fetchone()
            
            print(f"\n📈 HISTÓRICO (Ciclos cerrados):")
            print(f"    Días promedio por ciclo: {stats['dias_promedio']:.1f}")
            print(f"    Ganancia total acumulada: ${stats['ganancia_total']:.2f}")
            print(f"    ROI promedio: {stats['roi_promedio']:.2f}%")
    
    print("="*60)


# ===================================================================
# MENÚ DE CICLOS
# ===================================================================

def menu_ciclos():
    """Menú de gestión de ciclos"""
    
    while True:
        print("\n" + "="*60)
        print("GESTIÓN DE CICLOS")
        print("="*60)
        print("[1] Ver Ciclo Activo")
        print("[2] Crear Nuevo Ciclo")
        print("[3] Cerrar Ciclo Activo")
        print("[4] Extender Ciclo Activo")
        print("[5] Ver Estadísticas")
        print("[6] Historial de Ciclos")
        print("[7] Volver")
        print("="*60)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            ciclo = obtener_ciclo_activo()
            if ciclo:
                mostrar_info_ciclo(ciclo['id'])
            else:
                print("\n⚠️  No hay ciclo activo")
            input("\nPresiona Enter...")
        
        elif opcion == "2":
            try:
                dias = int(input("\n¿Cuántos días durará el ciclo? (15): ") or "15")
                crear_ciclo(dias)
            except ValueError:
                print("❌ Valor inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "3":
            ciclo = obtener_ciclo_activo()
            if ciclo:
                cerrar_ciclo(ciclo['id'])
            else:
                print("\n⚠️  No hay ciclo activo")
            input("\nPresiona Enter...")
        
        elif opcion == "4":
            ciclo = obtener_ciclo_activo()
            if ciclo:
                try:
                    dias = int(input("\n¿Cuántos días adicionales?: "))
                    extender_ciclo(ciclo['id'], dias)
                except ValueError:
                    print("❌ Valor inválido")
            else:
                print("\n⚠️  No hay ciclo activo")
            input("\nPresiona Enter...")
        
        elif opcion == "5":
            mostrar_estadisticas_completas()
            input("\nPresiona Enter...")
        
        elif opcion == "6":
            mostrar_historial_ciclos()
            input("\nPresiona Enter...")
        
        elif opcion == "7":
            break
        
        else:
            print("❌ Opción inválida")


def mostrar_historial_ciclos():
    """Muestra historial de todos los ciclos"""
    
    print("\n" + "="*60)
    print("HISTORIAL DE CICLOS")
    print("="*60)
    
    ciclos = db.execute_query("""
        SELECT * FROM ciclos
        ORDER BY id DESC
    """)
    
    if not ciclos:
        print("\n⚠️  No hay ciclos registrados")
        return
    
    for ciclo in ciclos:
        estado_emoji = "🔄" if ciclo['estado'] == 'activo' else "✅"
        
        print(f"\n{estado_emoji} Ciclo #{ciclo['id']} - {ciclo['estado'].upper()}")
        print(f"    Inicio: {ciclo['fecha_inicio']}")
        print(f"    Duración: {ciclo['dias_planificados']} días")
        print(f"    Inversión: ${ciclo['inversion_inicial']:.2f}")
        
        if ciclo['estado'] == 'cerrado':
            print(f"    Días operados: {ciclo['dias_operados']}")
            print(f"    Ganancia: ${ciclo['ganancia_total']:.2f}")
            print(f"    ROI: {ciclo['roi_total']:.2f}%")
            print(f"    Cerrado: {ciclo['fecha_cierre']}")
    
    print("="*60)


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_ciclos()
