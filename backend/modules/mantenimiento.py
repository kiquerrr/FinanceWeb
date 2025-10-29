# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE MANTENIMIENTO (CORREGIDO)
=============================================================================
Gestiona el mantenimiento de la base de datos y el sistema:
- Backups y restauración
- Verificación de integridad
- Limpieza de datos
- Logs y registros
- Optimización
✅ Ahora usa db_manager para conexiones seguras
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from core.logger import log
from core.db_manager import db


# ===================================================================
# DIRECTORIOS DE MANTENIMIENTO
# ===================================================================

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


# ===================================================================
# BACKUPS
# ===================================================================

def crear_backup():
    """Crea un backup completo de la base de datos"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"arbitraje_backup_{timestamp}.db"
    
    try:
        # Copiar archivo de base de datos directamente
        shutil.copy2('arbitraje.db', backup_file)
        
        # Calcular tamaño del backup
        tamaño_mb = backup_file.stat().st_size / (1024 * 1024)
        
        log.info(
            f"Backup creado exitosamente: {backup_file.name} ({tamaño_mb:.2f} MB)",
            categoria='general'
        )
        
        print(f"\n✅ Backup creado exitosamente")
        print(f"   Archivo: {backup_file.name}")
        print(f"   Tamaño: {tamaño_mb:.2f} MB")
        print(f"   Ubicación: {backup_file.absolute()}")
        
        return backup_file
        
    except Exception as e:
        log.error("Error al crear backup", str(e))
        print(f"❌ Error al crear backup: {e}")
        return None


def listar_backups():
    """Lista todos los backups disponibles"""
    
    backups = sorted(BACKUP_DIR.glob("arbitraje_backup_*.db"), reverse=True)
    
    if not backups:
        print("\n⚠️  No hay backups disponibles")
        return []
    
    print("\n" + "="*60)
    print("BACKUPS DISPONIBLES")
    print("="*60)
    
    backup_info = []
    for i, backup in enumerate(backups, 1):
        stat = backup.stat()
        tamaño_mb = stat.st_size / (1024 * 1024)
        fecha = datetime.fromtimestamp(stat.st_mtime)
        
        backup_info.append({
            'numero': i,
            'archivo': backup,
            'tamaño': tamaño_mb,
            'fecha': fecha
        })
        
        print(f"\n[{i}] {backup.name}")
        print(f"    Fecha: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Tamaño: {tamaño_mb:.2f} MB")
    
    print("="*60)
    return backup_info


def restaurar_backup(backup_file):
    """Restaura la base de datos desde un backup"""
    
    if not backup_file.exists():
        log.error("Backup no encontrado", str(backup_file))
        print(f"❌ Backup no encontrado: {backup_file}")
        return False
    
    print(f"\n⚠️  ADVERTENCIA: Esta acción sobrescribirá la base de datos actual")
    print(f"   Se restaurará desde: {backup_file.name}")
    
    confirmar = input("\n¿Estás seguro? (escribe 'CONFIRMAR' para continuar): ").strip()
    
    if confirmar != "CONFIRMAR":
        print("❌ Restauración cancelada")
        return False
    
    try:
        # Crear backup de seguridad antes de restaurar
        print("\nCreando backup de seguridad de la BD actual...")
        backup_seguridad = crear_backup()
        
        # Copiar el backup sobre la BD actual
        shutil.copy2(backup_file, 'arbitraje.db')
        
        log.info(f"Base de datos restaurada desde {backup_file.name}", categoria='general')
        
        print(f"\n✅ Base de datos restaurada exitosamente")
        if backup_seguridad:
            print(f"   Backup de seguridad guardado como: {backup_seguridad.name}")
        
        return True
        
    except Exception as e:
        log.error("Error al restaurar backup", str(e))
        print(f"❌ Error al restaurar: {e}")
        return False


def eliminar_backups_antiguos(dias=30):
    """Elimina backups más antiguos que X días"""
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    backups_eliminados = 0
    
    print(f"\nBuscando backups de más de {dias} días...")
    
    for backup in BACKUP_DIR.glob("*.db"):
        fecha_backup = datetime.fromtimestamp(backup.stat().st_mtime)
        
        if fecha_backup < fecha_limite:
            try:
                print(f"   Eliminando: {backup.name} ({fecha_backup.strftime('%Y-%m-%d')})")
                backup.unlink()
                backups_eliminados += 1
                log.info(f"Backup antiguo eliminado: {backup.name}", categoria='general')
            except Exception as e:
                print(f"   ⚠️  No se pudo eliminar {backup.name}: {e}")
    
    if backups_eliminados == 0:
        print(f"   ℹ️  No se encontraron backups de más de {dias} días")
    else:
        print(f"\n✅ {backups_eliminados} backup(s) antiguo(s) eliminado(s)")
    
    return backups_eliminados


# ===================================================================
# VERIFICACIÓN DE INTEGRIDAD
# ===================================================================

def verificar_integridad_bd():
    """Verifica la integridad de la base de datos"""
    
    print("\n" + "="*60)
    print("VERIFICANDO INTEGRIDAD DE LA BASE DE DATOS")
    print("="*60)
    
    errores = []
    
    with db.get_cursor(commit=False) as cursor:
        # 1. Verificar integridad de SQLite
        print("\n[1/6] Verificando integridad de SQLite...")
        cursor.execute("PRAGMA integrity_check")
        resultado = cursor.fetchone()[0]
        
        if resultado == "ok":
            print("   ✅ Integridad SQLite: OK")
        else:
            print(f"   ❌ Problemas de integridad: {resultado}")
            errores.append(f"SQLite integrity: {resultado}")
        
        # 2. Verificar tablas requeridas
        print("\n[2/6] Verificando tablas requeridas...")
        tablas_requeridas = [
            'config', 'ciclos', 'dias', 'criptomonedas',
            'boveda_ciclo', 'compras', 'ventas', 'efectivo_banco'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas_existentes = [t[0] for t in cursor.fetchall()]
        
        for tabla in tablas_requeridas:
            if tabla in tablas_existentes:
                print(f"   ✅ Tabla '{tabla}': OK")
            else:
                print(f"   ❌ Tabla '{tabla}': FALTA")
                errores.append(f"Tabla faltante: {tabla}")
        
        # 3. Verificar referencias foráneas
        print("\n[3/6] Verificando referencias foráneas...")
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        
        if not fk_errors:
            print("   ✅ Referencias foráneas: OK")
        else:
            print(f"   ❌ {len(fk_errors)} error(es) de referencias foráneas")
            errores.extend([f"FK error: {e}" for e in fk_errors])
        
        # 4. Verificar consistencia de datos
        print("\n[4/6] Verificando consistencia de datos...")
        
        # Verificar que las cantidades no sean negativas
        cursor.execute("SELECT COUNT(*) FROM boveda_ciclo WHERE cantidad < 0")
        cantidades_negativas = cursor.fetchone()[0]
        
        if cantidades_negativas == 0:
            print("   ✅ Cantidades en bóveda: OK")
        else:
            print(f"   ❌ {cantidades_negativas} cantidad(es) negativa(s) en bóveda")
            errores.append(f"Cantidades negativas: {cantidades_negativas}")
        
        # 5. Verificar huérfanos
        print("\n[5/6] Verificando registros huérfanos...")
        
        cursor.execute("""
            SELECT COUNT(*) FROM dias
            WHERE ciclo_id NOT IN (SELECT id FROM ciclos)
        """)
        dias_huerfanos = cursor.fetchone()[0]
        
        if dias_huerfanos == 0:
            print("   ✅ Días sin huérfanos: OK")
        else:
            print(f"   ❌ {dias_huerfanos} día(s) huérfano(s)")
            errores.append(f"Días huérfanos: {dias_huerfanos}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM ventas
            WHERE dia_id NOT IN (SELECT id FROM dias)
        """)
        ventas_huerfanas = cursor.fetchone()[0]
        
        if ventas_huerfanas == 0:
            print("   ✅ Ventas sin huérfanos: OK")
        else:
            print(f"   ❌ {ventas_huerfanas} venta(s) huérfana(s)")
            errores.append(f"Ventas huérfanas: {ventas_huerfanas}")
        
        # 6. Verificar configuración
        print("\n[6/6] Verificando configuración...")
        cursor.execute("SELECT COUNT(*) FROM config")
        tiene_config = cursor.fetchone()[0] > 0
        
        if tiene_config:
            print("   ✅ Configuración: OK")
        else:
            print("   ❌ No hay configuración")
            errores.append("Sin configuración")
    
    # Resumen
    print("\n" + "="*60)
    if errores:
        print(f"❌ {len(errores)} error(es) encontrado(s):")
        for error in errores:
            print(f"   • {error}")
    else:
        print("✅ BASE DE DATOS EN PERFECTO ESTADO")
    print("="*60)
    
    return len(errores) == 0


# ===================================================================
# OPTIMIZACIÓN
# ===================================================================

def optimizar_bd():
    """Optimiza la base de datos"""
    
    print("\n" + "="*60)
    print("OPTIMIZANDO BASE DE DATOS")
    print("="*60)
    
    try:
        with db.get_cursor(commit=True) as cursor:
            # 1. VACUUM - Reconstruye BD y recupera espacio
            print("\n[1/3] Ejecutando VACUUM...")
            cursor.execute("VACUUM")
            print("   ✅ VACUUM completado")
            
            # 2. ANALYZE - Actualiza estadísticas para optimizar queries
            print("\n[2/3] Ejecutando ANALYZE...")
            cursor.execute("ANALYZE")
            print("   ✅ ANALYZE completado")
            
            # 3. Verificar índices
            print("\n[3/3] Verificando índices...")
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
            """)
            indices = cursor.fetchall()
            print(f"   ✅ {len(indices)} índice(s) activos")
        
        log.info("Base de datos optimizada exitosamente", categoria='general')
        
        print("\n" + "="*60)
        print("✅ OPTIMIZACIÓN COMPLETADA")
        print("="*60)
        
        return True
        
    except Exception as e:
        log.error("Error al optimizar BD", str(e))
        print(f"\n❌ Error: {e}")
        return False


def obtener_info_sistema():
    """Obtiene información del sistema"""
    
    info = {}
    
    # Tamaño de BD
    if os.path.exists('arbitraje.db'):
        tamaño_bytes = os.path.getsize('arbitraje.db')
        info['tamaño_bd'] = tamaño_bytes / (1024 * 1024)  # MB
    else:
        info['tamaño_bd'] = 0
    
    # Número de backups
    backups = list(BACKUP_DIR.glob("*.db"))
    info['num_backups'] = len(backups)
    
    # Tamaño de logs
    tamaño_logs = 0
    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.log"):
            tamaño_logs += log_file.stat().st_size
    info['tamaño_logs'] = tamaño_logs / (1024 * 1024)  # MB
    
    # Estadísticas de BD
    with db.get_cursor(commit=False) as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM ciclos")
        info['total_ciclos'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM dias WHERE estado='cerrado'")
        info['dias_operados'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM ventas")
        info['total_ventas'] = cursor.fetchone()['total']
    
    return info


def mostrar_estadisticas_sistema():
    """Muestra estadísticas completas del sistema"""
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("="*60)
    
    info = obtener_info_sistema()
    
    print("\n📊 BASE DE DATOS:")
    print(f"   Tamaño: {info['tamaño_bd']:.2f} MB")
    print(f"   Ciclos registrados: {info['total_ciclos']}")
    print(f"   Días operados: {info['dias_operados']}")
    print(f"   Ventas totales: {info['total_ventas']}")
    
    print("\n💾 BACKUPS:")
    print(f"   Backups disponibles: {info['num_backups']}")
    if info['num_backups'] > 0:
        backups = list(BACKUP_DIR.glob("*.db"))
        ultimo = max(backups, key=lambda x: x.stat().st_mtime)
        fecha_ultimo = datetime.fromtimestamp(ultimo.stat().st_mtime)
        print(f"   Último backup: {fecha_ultimo.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📝 LOGS:")
    print(f"   Tamaño total: {info['tamaño_logs']:.2f} MB")
    if LOGS_DIR.exists():
        logs = list(LOGS_DIR.glob("*.log"))
        print(f"   Archivos de log: {len(logs)}")
    
    # Espacio en disco
    import shutil as sh
    total, usado, libre = sh.disk_usage(".")
    print("\n💿 ESPACIO EN DISCO:")
    print(f"   Total: {total // (2**30)} GB")
    print(f"   Usado: {usado // (2**30)} GB")
    print(f"   Libre: {libre // (2**30)} GB")
    
    print("="*60)


# ===================================================================
# LIMPIEZA
# ===================================================================

def limpiar_logs_antiguos(dias=30):
    """Limpia entradas antiguas de los logs"""
    
    print(f"\nLimpiando entradas de logs de más de {dias} días...")
    
    # Esta función requeriría procesar cada archivo de log
    # Por simplicidad, solo mostramos un mensaje
    print("⚠️  Función no implementada completamente")
    print("   Se recomienda hacer backup y eliminar logs manualmente si es necesario")
    
    return False


def limpiar_datos_ciclos_antiguos():
    """Permite eliminar datos de ciclos antiguos"""
    
    print("\n" + "="*60)
    print("LIMPIEZA DE CICLOS ANTIGUOS")
    print("="*60)
    
    # Listar ciclos cerrados
    ciclos = db.execute_query("""
        SELECT * FROM ciclos 
        WHERE estado = 'cerrado'
        ORDER BY fecha_cierre DESC
    """)
    
    if not ciclos:
        print("\n⚠️  No hay ciclos cerrados para limpiar")
        return False
    
    print(f"\nCiclos cerrados ({len(ciclos)}):")
    for ciclo in ciclos:
        print(f"\n  Ciclo #{ciclo['id']}")
        print(f"    Cerrado: {ciclo['fecha_cierre']}")
        print(f"    Días operados: {ciclo['dias_operados']}")
        print(f"    Ganancia: ${ciclo['ganancia_total']:.2f}")
    
    print("\n⚠️  ADVERTENCIA: Esto eliminará PERMANENTEMENTE los datos del ciclo")
    print("   Incluye: días, ventas, compras relacionadas")
    print("\n💡 Recomendación: Crea un backup antes de continuar")
    
    try:
        ciclo_id = int(input("\nID del ciclo a eliminar (0 para cancelar): "))
        
        if ciclo_id == 0:
            print("❌ Operación cancelada")
            return False
        
        confirmar = input(f"\n¿Eliminar ciclo #{ciclo_id}? (escribe 'ELIMINAR'): ").strip()
        
        if confirmar != "ELIMINAR":
            print("❌ Operación cancelada")
            return False
        
        # Crear backup primero
        print("\nCreando backup de seguridad...")
        crear_backup()
        
        # Eliminar en orden correcto (respetando foreign keys)
        with db.transaction() as conn:
            cursor = conn.cursor()
            
            # Obtener IDs de días
            cursor.execute("SELECT id FROM dias WHERE ciclo_id = ?", (ciclo_id,))
            dias_ids = [row['id'] for row in cursor.fetchall()]
            
            # Eliminar ventas
            for dia_id in dias_ids:
                cursor.execute("DELETE FROM ventas WHERE dia_id = ?", (dia_id,))
            
            # Eliminar efectivo
            cursor.execute("DELETE FROM efectivo_banco WHERE ciclo_id = ?", (ciclo_id,))
            
            # Eliminar días
            cursor.execute("DELETE FROM dias WHERE ciclo_id = ?", (ciclo_id,))
            
            # Eliminar compras
            cursor.execute("DELETE FROM compras WHERE ciclo_id = ?", (ciclo_id,))
            
            # Eliminar bóveda
            cursor.execute("DELETE FROM boveda_ciclo WHERE ciclo_id = ?", (ciclo_id,))
            
            # Eliminar ciclo
            cursor.execute("DELETE FROM ciclos WHERE id = ?", (ciclo_id,))
        
        log.info(f"Ciclo #{ciclo_id} eliminado", categoria='general')
        
        print(f"\n✅ Ciclo #{ciclo_id} eliminado exitosamente")
        return True
        
    except ValueError:
        print("❌ ID inválido")
        return False
    except Exception as e:
        log.error("Error al eliminar ciclo", str(e))
        print(f"❌ Error: {e}")
        return False


# ===================================================================
# REPARACIONES
# ===================================================================

def reparar_inconsistencias():
    """Intenta reparar inconsistencias en la BD"""
    
    print("\n" + "="*60)
    print("REPARANDO INCONSISTENCIAS")
    print("="*60)
    
    reparaciones = 0
    
    try:
        with db.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. Eliminar registros huérfanos en días
            print("\n[1/3] Buscando días huérfanos...")
            cursor.execute("""
                DELETE FROM dias
                WHERE ciclo_id NOT IN (SELECT id FROM ciclos)
            """)
            eliminados = cursor.connection.total_changes
            if eliminados > 0:
                print(f"   ✅ {eliminados} día(s) huérfano(s) eliminado(s)")
                reparaciones += eliminados
            else:
                print("   ✅ No hay días huérfanos")
            
            # 2. Eliminar ventas huérfanas
            print("\n[2/3] Buscando ventas huérfanas...")
            cursor.execute("""
                DELETE FROM ventas
                WHERE dia_id NOT IN (SELECT id FROM dias)
            """)
            eliminados = cursor.connection.total_changes
            if eliminados > 0:
                print(f"   ✅ {eliminados} venta(s) huérfana(s) eliminada(s)")
                reparaciones += eliminados
            else:
                print("   ✅ No hay ventas huérfanas")
            
            # 3. Corregir cantidades negativas (poner en 0)
            print("\n[3/3] Corrigiendo cantidades negativas...")
            cursor.execute("""
                UPDATE boveda_ciclo
                SET cantidad = 0
                WHERE cantidad < 0
            """)
            corregidos = cursor.connection.total_changes
            if corregidos > 0:
                print(f"   ✅ {corregidos} cantidad(es) corregida(s)")
                reparaciones += corregidos
            else:
                print("   ✅ No hay cantidades negativas")
        
        print("\n" + "="*60)
        if reparaciones > 0:
            print(f"✅ {reparaciones} reparación(es) realizada(s)")
            log.info(f"{reparaciones} inconsistencias reparadas", categoria='general')
        else:
            print("✅ No se encontraron inconsistencias")
        print("="*60)
        
        return True
        
    except Exception as e:
        log.error("Error al reparar inconsistencias", str(e))
        print(f"\n❌ Error: {e}")
        return False


# ===================================================================
# MENÚ DE MANTENIMIENTO
# ===================================================================

def menu_mantenimiento():
    """Menú principal de mantenimiento"""
    
    while True:
        print("\n" + "="*60)
        print("MANTENIMIENTO DEL SISTEMA")
        print("="*60)
        print("[1] Crear Backup")
        print("[2] Restaurar Backup")
        print("[3] Listar Backups")
        print("[4] Eliminar Backups Antiguos")
        print("[5] Verificar Integridad")
        print("[6] Reparar Inconsistencias")
        print("[7] Optimizar Base de Datos")
        print("[8] Limpiar Ciclos Antiguos")
        print("[9] Estadísticas del Sistema")
        print("[10] Volver")
        print("="*60)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            crear_backup()
            input("\nPresiona Enter...")
        
        elif opcion == "2":
            backups = listar_backups()
            if backups:
                try:
                    num = int(input("\nNúmero del backup a restaurar: "))
                    if 1 <= num <= len(backups):
                        restaurar_backup(backups[num-1]['archivo'])
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Entrada inválida")
            input("\nPresiona Enter...")
        
        elif opcion == "3":
            listar_backups()
            input("\nPresiona Enter...")
        
        elif opcion == "4":
            try:
                dias = int(input("\n¿Eliminar backups de más de cuántos días? (30): ") or "30")
                eliminar_backups_antiguos(dias)
            except ValueError:
                print("❌ Valor inválido")
            input("\nPresiona Enter...")
        
        elif opcion == "5":
            verificar_integridad_bd()
            input("\nPresiona Enter...")
        
        elif opcion == "6":
            reparar_inconsistencias()
            input("\nPresiona Enter...")
        
        elif opcion == "7":
            optimizar_bd()
            input("\nPresiona Enter...")
        
        elif opcion == "8":
            limpiar_datos_ciclos_antiguos()
            input("\nPresiona Enter...")
        
        elif opcion == "9":
            mostrar_estadisticas_sistema()
            input("\nPresiona Enter...")
        
        elif opcion == "10":
            break
        
        else:
            print("❌ Opción inválida")


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_mantenimiento()
