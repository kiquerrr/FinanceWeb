# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE CONFIGURACIÓN (CORREGIDO)
=============================================================================
Gestiona todas las configuraciones del sistema:
- Comisiones (manuales y por API)
- Ganancias objetivo
- APIs y plataformas
- Parámetros del sistema
✅ Ahora usa db_manager para conexiones seguras
"""

import json
from datetime import datetime
from core.logger import log
from core.db_manager import db


# ===================================================================
# TABLA DE CONFIGURACIÓN
# ===================================================================

def inicializar_tablas_config():
    """Crea las tablas de configuración si no existen"""
    
    with db.get_cursor(commit=True) as cursor:
        # Tabla de configuración general
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                comision_default REAL DEFAULT 0.35,
                ganancia_neta_default REAL DEFAULT 2.0,
                modo_comision TEXT DEFAULT 'manual',
                api_comision_activa INTEGER DEFAULT 0,
                limite_ventas_min INTEGER DEFAULT 3,
                limite_ventas_max INTEGER DEFAULT 5,
                actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de APIs configuradas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apis_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                plataforma TEXT NOT NULL,
                api_key TEXT,
                api_secret TEXT,
                activa INTEGER DEFAULT 1,
                tipo TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_actualizacion TIMESTAMP
            )
        """)
        
        # Tabla de comisiones por plataforma
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comisiones_plataforma (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plataforma TEXT NOT NULL,
                tipo_operacion TEXT NOT NULL,
                comision REAL NOT NULL,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar config por defecto si no existe
        cursor.execute("SELECT COUNT(*) as total FROM config")
        if cursor.fetchone()['total'] == 0:
            cursor.execute("""
                INSERT INTO config (id, comision_default, ganancia_neta_default)
                VALUES (1, 0.35, 2.0)
            """)
    
    log.info("Tablas de configuración inicializadas", categoria='general')


# ===================================================================
# CONFIGURACIÓN DE COMISIONES
# ===================================================================

def obtener_comision_actual():
    """Obtiene la comisión configurada actualmente"""
    return db.execute_query("""
        SELECT comision_default, modo_comision, api_comision_activa
        FROM config WHERE id = 1
    """, fetch_one=True)


def modificar_comision_manual(nueva_comision):
    """Modifica la comisión manualmente"""
    
    if nueva_comision < 0 or nueva_comision > 100:
        log.error("Comisión inválida", f"Valor: {nueva_comision}%")
        return False
    
    comision_anterior = obtener_comision_actual()['comision_default']
    
    db.execute_update("""
        UPDATE config SET
            comision_default = ?,
            modo_comision = 'manual',
            api_comision_activa = 0,
            actualizado = datetime('now')
        WHERE id = 1
    """, (nueva_comision,))
    
    log.info(
        f"Comisión actualizada manualmente: {comision_anterior}% → {nueva_comision}%",
        categoria='general'
    )
    
    print(f"✅ Comisión actualizada: {nueva_comision}%")
    return True


def configurar_api_comision(plataforma, api_key=None, api_secret=None):
    """Configura API para obtener comisiones automáticamente"""
    
    # Verificar si ya existe
    existe = db.execute_query("""
        SELECT id FROM apis_config
        WHERE plataforma = ? AND tipo = 'comision'
    """, (plataforma,), fetch_one=True)
    
    if existe:
        db.execute_update("""
            UPDATE apis_config SET
                api_key = ?,
                api_secret = ?,
                activa = 1,
                ultima_actualizacion = datetime('now')
            WHERE id = ?
        """, (api_key, api_secret, existe['id']))
    else:
        db.execute_update("""
            INSERT INTO apis_config (nombre, plataforma, api_key, api_secret, tipo, activa)
            VALUES (?, ?, ?, ?, 'comision', 1)
        """, (f"API Comisiones {plataforma}", plataforma, api_key, api_secret))
    
    log.info(f"API de comisiones configurada para {plataforma}", categoria='general')
    print(f"✅ API configurada para obtener comisiones de {plataforma}")
    return True


def obtener_comision_desde_api(plataforma):
    """
    Obtiene la comisión actual desde la API de la plataforma
    
    NOTA: Esta es una función esqueleto. Implementar según cada API.
    """
    
    # Obtener configuración de API
    api_config = db.execute_query("""
        SELECT api_key, api_secret
        FROM apis_config
        WHERE plataforma = ? AND tipo = 'comision' AND activa = 1
    """, (plataforma,), fetch_one=True)
    
    if not api_config:
        log.advertencia(f"No hay API configurada para {plataforma}", categoria='general')
        return None
    
    # TODO: Implementar llamada a API real según la plataforma
    # Ejemplo para Binance P2P:
    # import requests
    # response = requests.get('https://api.binance.com/api/v3/tradeFee')
    # comision = response.json()['tradeFee'][0]['taker']
    
    log.info(f"Intentando obtener comisión desde API de {plataforma}", categoria='general')
    
    # Por ahora, retornar None (no implementado)
    return None


def actualizar_comision_automatica():
    """Actualiza la comisión desde la API configurada"""
    
    config = obtener_comision_actual()
    
    if config['modo_comision'] != 'api' or not config['api_comision_activa']:
        print("⚠️  Modo API no está activo")
        return False
    
    # Obtener APIs activas
    apis = db.execute_query("""
        SELECT plataforma FROM apis_config
        WHERE tipo = 'comision' AND activa = 1
    """)
    
    if not apis:
        print("⚠️  No hay APIs configuradas")
        return False
    
    # Intentar obtener comisión de la primera API activa
    comision_obtenida = obtener_comision_desde_api(apis[0]['plataforma'])
    
    if comision_obtenida:
        db.execute_update("""
            UPDATE config SET
                comision_default = ?,
                actualizado = datetime('now')
            WHERE id = 1
        """, (comision_obtenida,))
        
        print(f"✅ Comisión actualizada desde API: {comision_obtenida}%")
        log.info(f"Comisión actualizada automáticamente: {comision_obtenida}%", categoria='general')
        return True
    else:
        print("❌ No se pudo obtener comisión desde API")
        print("   Usando comisión manual como respaldo")
        log.advertencia("API de comisión no disponible, usando manual", categoria='general')
        return False


# ===================================================================
# CONFIGURACIÓN DE GANANCIA OBJETIVO
# ===================================================================

def obtener_ganancia_objetivo():
    """Obtiene la ganancia objetivo configurada"""
    resultado = db.execute_query(
        "SELECT ganancia_neta_default FROM config WHERE id = 1",
        fetch_one=True
    )
    return resultado['ganancia_neta_default']


def modificar_ganancia_objetivo(nueva_ganancia):
    """Modifica la ganancia neta objetivo por defecto"""
    
    if nueva_ganancia < 0 or nueva_ganancia > 100:
        log.error("Ganancia objetivo inválida", f"Valor: {nueva_ganancia}%")
        return False
    
    ganancia_anterior = obtener_ganancia_objetivo()
    
    db.execute_update("""
        UPDATE config SET
            ganancia_neta_default = ?,
            actualizado = datetime('now')
        WHERE id = 1
    """, (nueva_ganancia,))
    
    log.info(
        f"Ganancia objetivo actualizada: {ganancia_anterior}% → {nueva_ganancia}%",
        categoria='general'
    )
    
    print(f"✅ Ganancia objetivo actualizada: {nueva_ganancia}%")
    return True


# ===================================================================
# LÍMITES DE VENTAS
# ===================================================================

def obtener_limites_ventas():
    """Obtiene los límites de ventas configurados"""
    return db.execute_query("""
        SELECT limite_ventas_min, limite_ventas_max
        FROM config WHERE id = 1
    """, fetch_one=True)


def modificar_limites_ventas(minimo, maximo):
    """Modifica los límites de ventas por día"""
    
    if minimo < 0 or maximo < minimo:
        log.error("Límites inválidos", f"Min: {minimo}, Max: {maximo}")
        print("❌ Límites inválidos")
        return False
    
    db.execute_update("""
        UPDATE config SET
            limite_ventas_min = ?,
            limite_ventas_max = ?,
            actualizado = datetime('now')
        WHERE id = 1
    """, (minimo, maximo))
    
    log.info(f"Límites de ventas actualizados: {minimo}-{maximo}", categoria='general')
    print(f"✅ Límites actualizados: {minimo}-{maximo} ventas/día")
    return True


# ===================================================================
# GESTIÓN DE APIs
# ===================================================================

def listar_apis_configuradas():
    """Lista todas las APIs configuradas"""
    return db.execute_query("""
        SELECT * FROM apis_config
        ORDER BY activa DESC, plataforma
    """)


def agregar_api_plataforma(nombre, plataforma, api_key, api_secret, tipo='trading'):
    """Agrega una nueva API al sistema"""
    
    db.execute_update("""
        INSERT INTO apis_config (nombre, plataforma, api_key, api_secret, tipo, activa)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (nombre, plataforma, api_key, api_secret, tipo))
    
    log.info(f"Nueva API agregada: {nombre} ({plataforma})", categoria='general')
    print(f"✅ API agregada: {nombre}")
    return True


def activar_desactivar_api(api_id, activar=True):
    """Activa o desactiva una API"""
    
    estado = 1 if activar else 0
    
    db.execute_update("""
        UPDATE apis_config SET
            activa = ?,
            ultima_actualizacion = datetime('now')
        WHERE id = ?
    """, (estado, api_id))
    
    accion = "activada" if activar else "desactivada"
    log.info(f"API #{api_id} {accion}", categoria='general')
    print(f"✅ API {accion}")
    return True


def eliminar_api(api_id):
    """Elimina una API del sistema"""
    
    db.execute_update("DELETE FROM apis_config WHERE id = ?", (api_id,))
    
    log.info(f"API #{api_id} eliminada", categoria='general')
    print(f"✅ API eliminada")
    return True


# ===================================================================
# MENÚ DE CONFIGURACIÓN
# ===================================================================

def menu_configuracion():
    """Menú principal de configuración"""
    
    while True:
        print("\n" + "="*60)
        print("CONFIGURACIÓN DEL SISTEMA")
        print("="*60)
        print("[1] Configurar Comisión")
        print("[2] Configurar Ganancia Objetivo")
        print("[3] Configurar Límites de Ventas")
        print("[4] Gestionar APIs")
        print("[5] Ver Todas las Configuraciones")
        print("[6] Exportar Configuración")
        print("[7] Importar Configuración")
        print("[8] Volver")
        print("="*60)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            submenu_comision()
        
        elif opcion == "2":
            submenu_ganancia()
        
        elif opcion == "3":
            submenu_limites()
        
        elif opcion == "4":
            submenu_apis()
        
        elif opcion == "5":
            mostrar_todas_configuraciones()
        
        elif opcion == "6":
            archivo = input("\nNombre del archivo (config_backup.json): ").strip() or "config_backup.json"
            exportar_configuracion(archivo)
            input("\nPresiona Enter...")
        
        elif opcion == "7":
            archivo = input("\nNombre del archivo (config_backup.json): ").strip() or "config_backup.json"
            importar_configuracion(archivo)
            input("\nPresiona Enter...")
        
        elif opcion == "8":
            break
        
        else:
            print("❌ Opción inválida")


def submenu_comision():
    """Submenú para configurar comisión"""
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE COMISIÓN")
    print("="*60)
    
    config = obtener_comision_actual()
    print(f"\nComisión actual: {config['comision_default']}%")
    print(f"Modo: {config['modo_comision']}")
    
    print("\n[1] Cambiar comisión manualmente")
    print("[2] Configurar API de comisiones")
    print("[3] Actualizar desde API")
    print("[4] Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        try:
            nueva = float(input("\nNueva comisión (%): "))
            modificar_comision_manual(nueva)
        except ValueError:
            print("❌ Valor inválido")
    
    elif opcion == "2":
        plataforma = input("\nPlataforma (Binance/Bybit/etc): ").strip()
        api_key = input("API Key: ").strip()
        api_secret = input("API Secret: ").strip()
        configurar_api_comision(plataforma, api_key, api_secret)
    
    elif opcion == "3":
        actualizar_comision_automatica()
    
    input("\nPresiona Enter...")


def submenu_ganancia():
    """Submenú para configurar ganancia objetivo"""
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE GANANCIA OBJETIVO")
    print("="*60)
    
    ganancia_actual = obtener_ganancia_objetivo()
    print(f"\nGanancia objetivo actual: {ganancia_actual}%")
    print("(Este es el % de ganancia neta que buscas en cada operación)")
    
    try:
        nueva = float(input("\nNueva ganancia objetivo (%): "))
        modificar_ganancia_objetivo(nueva)
    except ValueError:
        print("❌ Valor inválido")
    
    input("\nPresiona Enter...")


def submenu_apis():
    """Submenú para gestionar APIs"""
    
    while True:
        print("\n" + "="*60)
        print("GESTIÓN DE APIs")
        print("="*60)
        
        apis = listar_apis_configuradas()
        
        if apis:
            print("\nAPIs configuradas:")
            for api in apis:
                estado = "✅" if api['activa'] else "❌"
                print(f"{estado} [{api['id']}] {api['nombre']} - {api['plataforma']} ({api['tipo']})")
        else:
            print("\n⚠️  No hay APIs configuradas")
        
        print("\n" + "="*60)
        print("[1] Agregar Nueva API")
        print("[2] Activar/Desactivar API")
        print("[3] Eliminar API")
        print("[4] Volver")
        print("="*60)
        
        opcion = input("Selecciona: ").strip()
        
        if opcion == "1":
            agregar_api_menu()
        elif opcion == "2" and apis:
            activar_desactivar_api_menu(apis)
        elif opcion == "3" and apis:
            eliminar_api_menu(apis)
        elif opcion == "4":
            break
        else:
            print("❌ Opción inválida")


def agregar_api_menu():
    """Menú para agregar una nueva API"""
    
    print("\n" + "="*60)
    print("AGREGAR NUEVA API")
    print("="*60)
    
    nombre = input("Nombre de la API: ").strip()
    plataforma = input("Plataforma (Binance, Bybit, etc): ").strip()
    
    print("\nTipo de API:")
    print("[1] Trading")
    print("[2] Datos de mercado")
    print("[3] Comisiones")
    
    tipo_opcion = input("Selecciona: ").strip()
    tipos = {"1": "trading", "2": "market_data", "3": "comision"}
    tipo = tipos.get(tipo_opcion, "trading")
    
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    agregar_api_plataforma(nombre, plataforma, api_key, api_secret, tipo)
    input("\nPresiona Enter para continuar...")


def activar_desactivar_api_menu(apis):
    """Menú para activar/desactivar API"""
    
    try:
        api_id = int(input("\nID de la API: "))
        estado = input("¿Activar? (s/n): ").lower()
        activar = (estado == 's')
        activar_desactivar_api(api_id, activar)
        print("✅ Estado actualizado")
    except ValueError:
        print("❌ ID inválido")
    
    input("\nPresiona Enter para continuar...")


def eliminar_api_menu(apis):
    """Menú para eliminar API"""
    
    try:
        api_id = int(input("\nID de la API a eliminar: "))
        confirmar = input("¿Estás seguro? (s/n): ").lower()
        if confirmar == 's':
            eliminar_api(api_id)
    except ValueError:
        print("❌ ID inválido")
    
    input("\nPresiona Enter para continuar...")


def submenu_limites():
    """Submenú para configurar límites de ventas"""
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE LÍMITES DE VENTAS")
    print("="*60)
    
    limites = obtener_limites_ventas()
    print(f"\nLímites actuales: {limites['limite_ventas_min']} - {limites['limite_ventas_max']} ventas/día")
    print("\nEstos límites ayudan a evitar bloqueos bancarios")
    
    try:
        minimo = int(input("\nNuevo mínimo: "))
        maximo = int(input("Nuevo máximo: "))
        modificar_limites_ventas(minimo, maximo)
    except ValueError:
        print("❌ Valores inválidos")
    
    input("\nPresiona Enter para continuar...")


def mostrar_todas_configuraciones():
    """Muestra todas las configuraciones del sistema"""
    
    try:
        config = obtener_comision_actual()
        ganancia = obtener_ganancia_objetivo()
        limites = obtener_limites_ventas()
        apis = listar_apis_configuradas()
        
        print("\n" + "="*60)
        print("CONFIGURACIONES DEL SISTEMA")
        print("="*60)
        
        print("\n💰 COMISIONES:")
        if config:
            print(f"   Comisión actual: {config['comision_default']}%")
            print(f"   Modo: {config['modo_comision']}")
            print(f"   API activa: {'Sí' if config['api_comision_activa'] else 'No'}")
        else:
            print("   ⚠️  No hay configuración de comisiones")
        
        print("\n📈 GANANCIAS:")
        if ganancia is not None:
            print(f"   Ganancia objetivo: {ganancia}%")
        else:
            print("   ⚠️  No hay ganancia objetivo configurada")
        
        print("\n🔢 LÍMITES:")
        if limites:
            print(f"   Ventas por día: {limites['limite_ventas_min']} - {limites['limite_ventas_max']}")
        else:
            print("   ⚠️  No hay límites configurados")
        
        print("\n🔌 APIs CONFIGURADAS:")
        if apis and len(apis) > 0:
            for api in apis:
                estado = "Activa" if api['activa'] else "Inactiva"
                print(f"   • {api['nombre']} ({api['plataforma']}) - {estado}")
                print(f"     Tipo: {api['tipo']}")
        else:
            print("   No hay APIs configuradas")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error al mostrar configuraciones: {e}")
        log.error("Error en mostrar_todas_configuraciones", str(e))
    
    input("\nPresiona Enter para continuar...")


# ===================================================================
# EXPORTAR E IMPORTAR CONFIGURACIÓN
# ===================================================================

def exportar_configuracion(archivo="config_backup.json"):
    """Exporta la configuración a un archivo JSON"""
    
    config = obtener_comision_actual()
    ganancia = obtener_ganancia_objetivo()
    limites = obtener_limites_ventas()
    apis = listar_apis_configuradas()
    
    datos = {
        "comision": {
            "valor": config['comision_default'],
            "modo": config['modo_comision'],
            "api_activa": bool(config['api_comision_activa'])
        },
        "ganancia_objetivo": ganancia,
        "limites_ventas": {
            "minimo": limites['limite_ventas_min'],
            "maximo": limites['limite_ventas_max']
        },
        "apis": [
            {
                "nombre": api['nombre'],
                "plataforma": api['plataforma'],
                "tipo": api['tipo'],
                "activa": bool(api['activa'])
            }
            for api in apis
        ],
        "fecha_exportacion": datetime.now().isoformat()
    }
    
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    
    log.info(f"Configuración exportada a {archivo}", categoria='general')
    print(f"✅ Configuración exportada a {archivo}")
    return True


def importar_configuracion(archivo="config_backup.json"):
    """Importa configuración desde un archivo JSON"""
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Importar comisión
        modificar_comision_manual(datos['comision']['valor'])
        
        # Importar ganancia
        modificar_ganancia_objetivo(datos['ganancia_objetivo'])
        
        # Importar límites
        modificar_limites_ventas(
            datos['limites_ventas']['minimo'],
            datos['limites_ventas']['maximo']
        )
        
        log.info(f"Configuración importada desde {archivo}", categoria='general')
        print(f"✅ Configuración importada desde {archivo}")
        print("⚠️  Las APIs no se importan por seguridad (deben configurarse manualmente)")
        return True
        
    except FileNotFoundError:
        log.error(f"Archivo no encontrado: {archivo}")
        print(f"❌ Archivo no encontrado: {archivo}")
        return False
    except Exception as e:
        log.error(f"Error al importar configuración", str(e))
        print(f"❌ Error: {e}")
        return False


# ===================================================================
# INICIALIZACIÓN
# ===================================================================

# Inicializar tablas al importar el módulo
inicializar_tablas_config()


if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar el menú
    menu_configuracion()
