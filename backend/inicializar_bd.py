# -*- coding: utf-8 -*-
"""
=============================================================================
INICIALIZACIÓN DE BASE DE DATOS v3.0
=============================================================================
Crea y configura la base de datos desde cero
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


# ===================================================================
# CONFIGURACIÓN
# ===================================================================

DB_FILE = 'data/arbitraje.db'
BACKUP_DIR = Path('backups')
DATA_DIR = Path('data')

# Crear directorios si no existen
BACKUP_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ===================================================================
# FUNCIONES DE BACKUP
# ===================================================================

def hacer_backup_si_existe():
    """Hace backup de la BD si ya existe"""
    
    if os.path.exists(DB_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f'arbitraje_backup_antes_reinicio_{timestamp}.db'
        
        print(f"\n⚠️  La base de datos ya existe")
        print(f"📁 Creando backup: {backup_file.name}")
        
        import shutil
        shutil.copy2(DB_FILE, backup_file)
        
        print("✅ Backup creado exitosamente")
        return True
    
    return False


# ===================================================================
# CREACIÓN DE TABLAS
# ===================================================================

def crear_tablas(conn):
    """Crea todas las tablas del sistema"""
    
    cursor = conn.cursor()
    
    print("\n📋 Creando tablas...")
    
    # Tabla de configuración
    print("   • config")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            comision_default REAL DEFAULT 0.35,
            ganancia_neta_default REAL DEFAULT 2.0,
            modo_comision TEXT DEFAULT 'manual',
            api_comision_activa INTEGER DEFAULT 0,
            limite_ventas_min INTEGER DEFAULT 5,
            limite_ventas_max INTEGER DEFAULT 8,
            actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de criptomonedas
    print("   • criptomonedas")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS criptomonedas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            simbolo TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            descripcion TEXT
        )
    """)
    
    # Tabla de ciclos
    print("   • ciclos")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ciclos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_inicio DATE NOT NULL,
            fecha_fin_estimada DATE NOT NULL,
            fecha_cierre TIMESTAMP,
            dias_planificados INTEGER NOT NULL,
            dias_operados INTEGER DEFAULT 0,
            inversion_inicial REAL DEFAULT 0,
            capital_final REAL,
            ganancia_total REAL DEFAULT 0,
            roi_total REAL,
            estado TEXT DEFAULT 'activo',
            CHECK(estado IN ('activo', 'cerrado'))
        )
    """)
    
    # Tabla de días
    print("   • dias")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo_id INTEGER NOT NULL,
            numero_dia INTEGER NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre TIMESTAMP,
            capital_inicial REAL NOT NULL,
            capital_final REAL,
            efectivo_recibido REAL DEFAULT 0,
            cripto_operada_id INTEGER,
            precio_publicado REAL,
            comisiones_pagadas REAL DEFAULT 0,
            ganancia_bruta REAL DEFAULT 0,
            ganancia_neta REAL DEFAULT 0,
            estado TEXT DEFAULT 'abierto',
            FOREIGN KEY (ciclo_id) REFERENCES ciclos(id),
            FOREIGN KEY (cripto_operada_id) REFERENCES criptomonedas(id),
            CHECK(estado IN ('abierto', 'cerrado'))
        )
    """)
    
    # Tabla de ventas
    print("   • ventas")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_id INTEGER NOT NULL,
            cripto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            costo_total REAL NOT NULL,
            monto_venta REAL NOT NULL,
            comision REAL NOT NULL,
            efectivo_recibido REAL NOT NULL,
            ganancia_bruta REAL NOT NULL,
            ganancia_neta REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dia_id) REFERENCES dias(id),
            FOREIGN KEY (cripto_id) REFERENCES criptomonedas(id)
        )
    """)
    
    # Tabla de bóveda por ciclo
    print("   • boveda_ciclo")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boveda_ciclo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo_id INTEGER NOT NULL,
            cripto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL DEFAULT 0,
            precio_promedio REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (ciclo_id) REFERENCES ciclos(id),
            FOREIGN KEY (cripto_id) REFERENCES criptomonedas(id),
            UNIQUE(ciclo_id, cripto_id)
        )
    """)
    
    # Tabla de compras
    print("   • compras")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo_id INTEGER NOT NULL,
            cripto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            monto_usd REAL NOT NULL,
            tasa REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ciclo_id) REFERENCES ciclos(id),
            FOREIGN KEY (cripto_id) REFERENCES criptomonedas(id)
        )
    """)
    
    # Tabla de efectivo en banco
    print("   • efectivo_banco")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS efectivo_banco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo_id INTEGER NOT NULL,
            dia_id INTEGER,
            monto REAL NOT NULL,
            concepto TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ciclo_id) REFERENCES ciclos(id),
            FOREIGN KEY (dia_id) REFERENCES dias(id)
        )
    """)
    
    # Tabla de APIs configuradas
    print("   • apis_config")
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
    print("   • comisiones_plataforma")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comisiones_plataforma (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma TEXT NOT NULL,
            tipo_operacion TEXT NOT NULL,
            comision REAL NOT NULL,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de notas
    print("   • notas")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            referencia_id INTEGER,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            prioridad TEXT DEFAULT 'normal',
            etiquetas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TIMESTAMP,
            autor TEXT DEFAULT 'Operador'
        )
    """)
    
    # Tabla de alertas
    print("   • alertas")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nivel TEXT NOT NULL,
            titulo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            referencia_tipo TEXT,
            referencia_id INTEGER,
            leida INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_lectura TIMESTAMP
        )
    """)
    
    # Tabla de configuración de alertas
    print("   • config_alertas")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_alerta TEXT NOT NULL UNIQUE,
            activa INTEGER DEFAULT 1,
            umbral REAL,
            parametros TEXT
        )
    """)
    
    conn.commit()
    print("✅ Tablas creadas exitosamente")


def crear_indices(conn):
    """Crea índices para mejorar rendimiento"""
    
    cursor = conn.cursor()
    
    print("\n📊 Creando índices...")
    
    indices = [
        ("idx_dias_ciclo", "CREATE INDEX IF NOT EXISTS idx_dias_ciclo ON dias(ciclo_id)"),
        ("idx_ventas_dia", "CREATE INDEX IF NOT EXISTS idx_ventas_dia ON ventas(dia_id)"),
        ("idx_boveda_ciclo", "CREATE INDEX IF NOT EXISTS idx_boveda_ciclo ON boveda_ciclo(ciclo_id)"),
        ("idx_compras_ciclo", "CREATE INDEX IF NOT EXISTS idx_compras_ciclo ON compras(ciclo_id)"),
        ("idx_notas_tipo", "CREATE INDEX IF NOT EXISTS idx_notas_tipo ON notas(tipo)"),
        ("idx_notas_referencia", "CREATE INDEX IF NOT EXISTS idx_notas_referencia ON notas(tipo, referencia_id)"),
        ("idx_alertas_leida", "CREATE INDEX IF NOT EXISTS idx_alertas_leida ON alertas(leida)"),
    ]
    
    for nombre, query in indices:
        print(f"   • {nombre}")
        cursor.execute(query)
    
    conn.commit()
    print("✅ Índices creados exitosamente")


def insertar_datos_iniciales(conn):
    """Inserta datos iniciales del sistema"""
    
    cursor = conn.cursor()
    
    print("\n💾 Insertando datos iniciales...")
    
    # Configuración por defecto
    print("   • Configuración por defecto")
    cursor.execute("""
        INSERT INTO config (id, comision_default, ganancia_neta_default)
        VALUES (1, 0.35, 2.0)
    """)
    
    # Criptomonedas por defecto
    print("   • Criptomonedas")
    criptos = [
        ('Tether', 'USDT', 'stablecoin', 'Stablecoin vinculada al dólar estadounidense'),
        ('USD Coin', 'USDC', 'stablecoin', 'Stablecoin respaldada por dólares en reserva'),
        ('Binance USD', 'BUSD', 'stablecoin', 'Stablecoin emitida por Binance'),
        ('Bitcoin', 'BTC', 'criptomoneda', 'La primera y más conocida criptomoneda'),
        ('Ethereum', 'ETH', 'criptomoneda', 'Plataforma blockchain con contratos inteligentes'),
        ('Binance Coin', 'BNB', 'criptomoneda', 'Token nativo de Binance'),
        ('Dai', 'DAI', 'stablecoin', 'Stablecoin descentralizada'),
    ]
    
    cursor.executemany("""
        INSERT INTO criptomonedas (nombre, simbolo, tipo, descripcion)
        VALUES (?, ?, ?, ?)
    """, criptos)
    
    # Configuración de alertas por defecto
    print("   • Configuración de alertas")
    alertas_config = [
        ('dia_abierto_largo', 1, 24),
        ('limite_ventas', 1, None),
        ('capital_bajo', 1, 100),
        ('ganancia_negativa', 1, None),
        ('ciclo_por_terminar', 1, 3),
        ('sin_operar', 1, 3),
        ('objetivo_alcanzado', 1, None),
        ('rendimiento_bajo', 1, 1.0),
    ]
    
    cursor.executemany("""
        INSERT INTO config_alertas (tipo_alerta, activa, umbral)
        VALUES (?, ?, ?)
    """, alertas_config)
    
    conn.commit()
    print("✅ Datos iniciales insertados")


def verificar_integridad(conn):
    """Verifica la integridad de la base de datos"""
    
    cursor = conn.cursor()
    
    print("\n🔍 Verificando integridad...")
    
    cursor.execute("PRAGMA integrity_check")
    resultado = cursor.fetchone()[0]
    
    if resultado == "ok":
        print("✅ Integridad verificada: OK")
        return True
    else:
        print(f"❌ Problemas de integridad: {resultado}")
        return False


def mostrar_resumen(conn):
    """Muestra resumen de la base de datos creada"""
    
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("RESUMEN DE LA BASE DE DATOS")
    print("="*70)
    
    # Contar tablas
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    num_tablas = cursor.fetchone()[0]
    print(f"\n📋 Tablas creadas: {num_tablas}")
    
    # Listar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = cursor.fetchall()
    
    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {tabla[0]}: {count} registro(s)")
    
    # Contar índices
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    num_indices = cursor.fetchone()[0]
    print(f"\n📊 Índices creados: {num_indices}")
    
    # Tamaño de la BD
    tamaño = os.path.getsize(DB_FILE) / 1024  # KB
    print(f"\n💾 Tamaño de la BD: {tamaño:.2f} KB")
    print(f"📁 Ubicación: {Path(DB_FILE).absolute()}")
    
    print("\n" + "="*70)


# ===================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================

def inicializar_base_datos():
    """Inicializa la base de datos completa"""
    
    print("\n" + "="*70)
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║       INICIALIZACIÓN DE BASE DE DATOS - VERSIÓN 3.0              ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print("="*70)
    
    # Advertencia
    if os.path.exists(DB_FILE):
        print("\n⚠️  ADVERTENCIA: La base de datos ya existe")
        print("   Esta operación eliminará todos los datos actuales")
        
        confirmar = input("\n¿Deseas continuar? (escribe 'CONFIRMAR'): ").strip()
        
        if confirmar != "CONFIRMAR":
            print("\n❌ Operación cancelada")
            return False
        
        # Hacer backup
        hacer_backup_si_existe()
        
        # Eliminar BD actual
        print("\n🗑️  Eliminando base de datos actual...")
        os.remove(DB_FILE)
        print("✅ Base de datos eliminada")
    
    try:
        # Crear conexión
        print(f"\n🔨 Creando nueva base de datos: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Crear tablas
        crear_tablas(conn)
        
        # Crear índices
        crear_indices(conn)
        
        # Insertar datos iniciales
        insertar_datos_iniciales(conn)
        
        # Verificar integridad
        if not verificar_integridad(conn):
            print("\n❌ Error en la integridad de la base de datos")
            conn.close()
            return False
        
        # Mostrar resumen
        mostrar_resumen(conn)
        
        # Cerrar conexión
        conn.close()
        
        print("\n✅ ¡BASE DE DATOS INICIALIZADA CORRECTAMENTE!")
        print("\n🚀 Para iniciar el sistema:")
        print("   python main.py")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Error de SQLite: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False


# ===================================================================
# MENÚ INTERACTIVO
# ===================================================================

def menu_inicializacion():
    """Menú de opciones de inicialización"""
    
    print("\n" + "="*70)
    print("INICIALIZACIÓN DE BASE DE DATOS")
    print("="*70)
    print("\n[1] Inicializar base de datos (ELIMINA DATOS ACTUALES)")
    print("[2] Solo verificar estructura")
    print("[3] Salir")
    print("="*70)
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        inicializar_base_datos()
    elif opcion == "2":
        if os.path.exists(DB_FILE):
            conn = sqlite3.connect(DB_FILE)
            verificar_integridad(conn)
            mostrar_resumen(conn)
            conn.close()
        else:
            print("\n❌ No existe base de datos para verificar")
    elif opcion == "3":
        print("\n👋 ¡Hasta pronto!")
    else:
        print("\n❌ Opción inválida")


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    try:
        menu_inicializacion()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        input("\nPresiona Enter para salir...")