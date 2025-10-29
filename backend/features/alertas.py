# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE ALERTAS
=============================================================================
Sistema de alertas y notificaciones automáticas
Detecta situaciones importantes y notifica al usuario
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.db_manager import db
from core.queries import queries
from core.logger import log


# ===================================================================
# CREAR TABLA DE ALERTAS
# ===================================================================

def inicializar_tabla_alertas():
    """Crea las tablas de alertas si no existen"""
    
    with db.get_cursor(commit=True) as cursor:
        # Tabla de alertas generadas
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_alerta TEXT NOT NULL UNIQUE,
                activa INTEGER DEFAULT 1,
                umbral REAL,
                parametros TEXT
            )
        """)
        
        # Insertar configuraciones por defecto
        cursor.execute("""
            INSERT OR IGNORE INTO config_alertas (tipo_alerta, activa, umbral)
            VALUES 
                ('dia_abierto_largo', 1, 24),
                ('limite_ventas', 1, NULL),
                ('capital_bajo', 1, 100),
                ('ganancia_negativa', 1, NULL),
                ('ciclo_por_terminar', 1, 3),
                ('sin_operar', 1, 3),
                ('objetivo_alcanzado', 1, NULL),
                ('rendimiento_bajo', 1, 1.0)
        """)
    
    log.info("Sistema de alertas inicializado", categoria='general')


# Inicializar al importar
inicializar_tabla_alertas()


# ===================================================================
# CLASE DE GESTIÓN DE ALERTAS
# ===================================================================

class SistemaAlertas:
    """Sistema central de alertas"""
    
    NIVELES = {
        'info': '💡',
        'exito': '✅',
        'advertencia': '⚠️',
        'error': '❌',
        'critico': '🚨'
    }
    
    # ===================================================================
    # CREAR ALERTAS
    # ===================================================================
    
    @staticmethod
    def crear_alerta(tipo: str, nivel: str, titulo: str, mensaje: str,
                     referencia_tipo: Optional[str] = None,
                     referencia_id: Optional[int] = None) -> int:
        """
        Crea una nueva alerta
        
        Args:
            tipo: Tipo de alerta
            nivel: info, exito, advertencia, error, critico
            titulo: Título de la alerta
            mensaje: Mensaje detallado
            referencia_tipo: Tipo de referencia (ciclo, dia, etc)
            referencia_id: ID de la referencia
        
        Returns:
            int: ID de la alerta creada
        """
        alerta_id = db.execute_update("""
            INSERT INTO alertas (
                tipo, nivel, titulo, mensaje,
                referencia_tipo, referencia_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (tipo, nivel, titulo, mensaje, referencia_tipo, referencia_id))
        
        log.info(f"Alerta creada: {titulo}", categoria='alertas')
        
        return alerta_id
    
    # ===================================================================
    # VERIFICADORES DE ALERTAS
    # ===================================================================
    
    @staticmethod
    def verificar_dia_abierto_largo(ciclo_id: int):
        """Verifica si hay un día abierto por mucho tiempo"""
        
        config = db.execute_query("""
            SELECT umbral FROM config_alertas
            WHERE tipo_alerta = 'dia_abierto_largo' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        horas_limite = config['umbral']
        
        dia_abierto = db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ? AND estado = 'abierto'
        """, (ciclo_id,), fetch_one=True)
        
        if not dia_abierto:
            return
        
        fecha_inicio = datetime.strptime(dia_abierto['fecha'], '%Y-%m-%d %H:%M:%S')
        horas_transcurridas = (datetime.now() - fecha_inicio).total_seconds() / 3600
        
        if horas_transcurridas >= horas_limite:
            # Verificar si ya existe alerta
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'dia_abierto_largo'
                AND referencia_id = ?
                AND leida = 0
            """, (dia_abierto['id'],), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='dia_abierto_largo',
                    nivel='advertencia',
                    titulo='Día abierto por mucho tiempo',
                    mensaje=f"El día #{dia_abierto['numero_dia']} lleva {int(horas_transcurridas)} horas abierto. Considera cerrarlo.",
                    referencia_tipo='dia',
                    referencia_id=dia_abierto['id']
                )
    
    @staticmethod
    def verificar_limite_ventas(dia_id: int):
        """Verifica si se está acercando o pasando el límite de ventas"""
        
        config = db.execute_query("""
            SELECT activa FROM config_alertas
            WHERE tipo_alerta = 'limite_ventas' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        # Obtener límites
        limites = queries.obtener_limites_ventas()
        min_ventas, max_ventas = limites
        
        # Contar ventas del día
        num_ventas = queries.contar_ventas_dia(dia_id)
        
        # Alerta si alcanzó el máximo
        if num_ventas >= max_ventas:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'limite_ventas_max'
                AND referencia_id = ?
                AND leida = 0
            """, (dia_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='limite_ventas_max',
                    nivel='advertencia',
                    titulo='Límite máximo de ventas alcanzado',
                    mensaje=f"Has alcanzado el límite recomendado de {max_ventas} ventas por día. Considera cerrar el día para evitar bloqueos bancarios.",
                    referencia_tipo='dia',
                    referencia_id=dia_id
                )
        
        # Alerta si está cerca del máximo
        elif num_ventas >= max_ventas - 1:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'limite_ventas_cerca'
                AND referencia_id = ?
                AND leida = 0
            """, (dia_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='limite_ventas_cerca',
                    nivel='info',
                    titulo='Cerca del límite de ventas',
                    mensaje=f"Has realizado {num_ventas} ventas. El límite recomendado es {max_ventas}.",
                    referencia_tipo='dia',
                    referencia_id=dia_id
                )
    
    @staticmethod
    def verificar_capital_bajo(ciclo_id: int):
        """Verifica si el capital está bajo"""
        
        config = db.execute_query("""
            SELECT umbral FROM config_alertas
            WHERE tipo_alerta = 'capital_bajo' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        umbral = config['umbral']
        capital = queries.obtener_capital_boveda(ciclo_id)
        
        if capital <= umbral and capital > 0:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'capital_bajo'
                AND referencia_id = ?
                AND leida = 0
            """, (ciclo_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='capital_bajo',
                    nivel='advertencia',
                    titulo='Capital bajo en bóveda',
                    mensaje=f"El capital en bóveda es de ${capital:.2f}, por debajo del umbral de ${umbral:.2f}. Considera fondear la bóveda.",
                    referencia_tipo='ciclo',
                    referencia_id=ciclo_id
                )
    
    @staticmethod
    def verificar_ganancia_negativa(dia_id: int):
        """Verifica si hubo ganancia negativa (pérdida)"""
        
        config = db.execute_query("""
            SELECT activa FROM config_alertas
            WHERE tipo_alerta = 'ganancia_negativa' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        dia = db.execute_query(
            "SELECT * FROM dias WHERE id = ? AND estado = 'cerrado'",
            (dia_id,),
            fetch_one=True
        )
        
        if dia and dia['ganancia_neta'] and dia['ganancia_neta'] < 0:
            SistemaAlertas.crear_alerta(
                tipo='ganancia_negativa',
                nivel='error',
                titulo='Pérdida registrada',
                mensaje=f"El día #{dia['numero_dia']} cerró con pérdida de ${abs(dia['ganancia_neta']):.2f}. Revisa las operaciones.",
                referencia_tipo='dia',
                referencia_id=dia_id
            )
    
    @staticmethod
    def verificar_ciclo_por_terminar(ciclo_id: int):
        """Verifica si el ciclo está por terminar"""
        
        config = db.execute_query("""
            SELECT umbral FROM config_alertas
            WHERE tipo_alerta = 'ciclo_por_terminar' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        dias_limite = config['umbral']
        
        ciclo = queries.obtener_ciclo_por_id(ciclo_id)
        if not ciclo or ciclo['estado'] != 'activo':
            return
        
        # Calcular días restantes
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as dias_operados
                FROM dias WHERE ciclo_id = ?
            """, (ciclo_id,))
            dias_operados = cursor.fetchone()['dias_operados']
        
        dias_restantes = ciclo['dias_planificados'] - dias_operados
        
        if 0 < dias_restantes <= dias_limite:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'ciclo_por_terminar'
                AND referencia_id = ?
                AND leida = 0
            """, (ciclo_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='ciclo_por_terminar',
                    nivel='info',
                    titulo='Ciclo por terminar',
                    mensaje=f"El ciclo #{ciclo_id} tiene solo {dias_restantes} día(s) restante(s). Planifica el cierre o extensión.",
                    referencia_tipo='ciclo',
                    referencia_id=ciclo_id
                )
    
    @staticmethod
    def verificar_sin_operar(ciclo_id: int):
        """Verifica si lleva días sin operar"""
        
        config = db.execute_query("""
            SELECT umbral FROM config_alertas
            WHERE tipo_alerta = 'sin_operar' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        dias_limite = config['umbral']
        
        ultimo_dia = db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ?
            ORDER BY numero_dia DESC
            LIMIT 1
        """, (ciclo_id,), fetch_one=True)
        
        if not ultimo_dia:
            return
        
        if ultimo_dia['estado'] == 'abierto':
            return  # Hay un día abierto
        
        fecha_ultimo = datetime.strptime(ultimo_dia['fecha_cierre'], '%Y-%m-%d %H:%M:%S')
        dias_sin_operar = (datetime.now() - fecha_ultimo).days
        
        if dias_sin_operar >= dias_limite:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'sin_operar'
                AND referencia_id = ?
                AND leida = 0
                AND date(fecha_creacion) = date('now')
            """, (ciclo_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='sin_operar',
                    nivel='advertencia',
                    titulo='Días sin operar',
                    mensaje=f"Llevas {dias_sin_operar} días sin operar en el ciclo #{ciclo_id}. ¿Todo bien?",
                    referencia_tipo='ciclo',
                    referencia_id=ciclo_id
                )
    
    @staticmethod
    def verificar_objetivo_alcanzado(ciclo_id: int, objetivo_usd: float):
        """Verifica si se alcanzó un objetivo de ganancia"""
        
        config = db.execute_query("""
            SELECT activa FROM config_alertas
            WHERE tipo_alerta = 'objetivo_alcanzado' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        ciclo = queries.obtener_ciclo_por_id(ciclo_id)
        if not ciclo:
            return
        
        ganancia_total = db.execute_query("""
            SELECT COALESCE(SUM(ganancia_neta), 0) as total
            FROM dias WHERE ciclo_id = ? AND estado = 'cerrado'
        """, (ciclo_id,), fetch_one=True)['total']
        
        if ganancia_total >= objetivo_usd:
            alerta_existente = db.execute_query("""
                SELECT id FROM alertas
                WHERE tipo = 'objetivo_alcanzado'
                AND referencia_id = ?
                AND leida = 0
            """, (ciclo_id,), fetch_one=True)
            
            if not alerta_existente:
                SistemaAlertas.crear_alerta(
                    tipo='objetivo_alcanzado',
                    nivel='exito',
                    titulo='¡Objetivo alcanzado!',
                    mensaje=f"Has alcanzado tu objetivo de ${objetivo_usd:.2f}. Ganancia actual: ${ganancia_total:.2f}",
                    referencia_tipo='ciclo',
                    referencia_id=ciclo_id
                )
    
    @staticmethod
    def verificar_rendimiento_bajo(dia_id: int):
        """Verifica si el rendimiento del día fue bajo"""
        
        config = db.execute_query("""
            SELECT umbral FROM config_alertas
            WHERE tipo_alerta = 'rendimiento_bajo' AND activa = 1
        """, fetch_one=True)
        
        if not config:
            return
        
        umbral_pct = config['umbral']
        
        dia = db.execute_query(
            "SELECT * FROM dias WHERE id = ? AND estado = 'cerrado'",
            (dia_id,),
            fetch_one=True
        )
        
        if not dia or not dia['ganancia_neta']:
            return
        
        roi_dia = (dia['ganancia_neta'] / dia['capital_inicial'] * 100) if dia['capital_inicial'] > 0 else 0
        
        if 0 < roi_dia < umbral_pct:
            SistemaAlertas.crear_alerta(
                tipo='rendimiento_bajo',
                nivel='info',
                titulo='Rendimiento bajo',
                mensaje=f"El día #{dia['numero_dia']} tuvo un ROI de {roi_dia:.2f}%, por debajo del objetivo de {umbral_pct}%.",
                referencia_tipo='dia',
                referencia_id=dia_id
            )
    
    # ===================================================================
    # EJECUTAR TODAS LAS VERIFICACIONES
    # ===================================================================
    
    @staticmethod
    def verificar_todas(ciclo_id: Optional[int] = None):
        """
        Ejecuta todas las verificaciones de alertas
        
        Args:
            ciclo_id: ID del ciclo (si es None, usa el activo)
        """
        if ciclo_id is None:
            ciclo = queries.obtener_ciclo_activo()
            if not ciclo:
                return
            ciclo_id = ciclo['id']
        
        # Verificar día abierto largo
        SistemaAlertas.verificar_dia_abierto_largo(ciclo_id)
        
        # Verificar capital bajo
        SistemaAlertas.verificar_capital_bajo(ciclo_id)
        
        # Verificar ciclo por terminar
        SistemaAlertas.verificar_ciclo_por_terminar(ciclo_id)
        
        # Verificar sin operar
        SistemaAlertas.verificar_sin_operar(ciclo_id)
        
        # Verificar límite de ventas en día abierto
        dia_abierto = queries.obtener_dia_abierto(ciclo_id)
        if dia_abierto:
            SistemaAlertas.verificar_limite_ventas(dia_abierto['id'])
    
    # ===================================================================
    # CONSULTAR ALERTAS
    # ===================================================================
    
    @staticmethod
    def obtener_alertas_no_leidas(limite: int = 20):
        """Obtiene alertas no leídas"""
        return db.execute_query("""
            SELECT * FROM alertas
            WHERE leida = 0
            ORDER BY 
                CASE nivel
                    WHEN 'critico' THEN 1
                    WHEN 'error' THEN 2
                    WHEN 'advertencia' THEN 3
                    WHEN 'exito' THEN 4
                    WHEN 'info' THEN 5
                END,
                fecha_creacion DESC
            LIMIT ?
        """, (limite,))
    
    @staticmethod
    def obtener_alertas_recientes(horas: int = 24, limite: int = 50):
        """Obtiene alertas recientes"""
        return db.execute_query("""
            SELECT * FROM alertas
            WHERE datetime(fecha_creacion) >= datetime('now', '-' || ? || ' hours')
            ORDER BY fecha_creacion DESC
            LIMIT ?
        """, (horas, limite))
    
    @staticmethod
    def contar_alertas_no_leidas():
        """Cuenta alertas no leídas"""
        resultado = db.execute_query(
            "SELECT COUNT(*) as total FROM alertas WHERE leida = 0",
            fetch_one=True
        )
        return resultado['total']
    
    @staticmethod
    def marcar_leida(alerta_id: int):
        """Marca una alerta como leída"""
        db.execute_update("""
            UPDATE alertas
            SET leida = 1, fecha_lectura = datetime('now')
            WHERE id = ?
        """, (alerta_id,))
    
    @staticmethod
    def marcar_todas_leidas():
        """Marca todas las alertas como leídas"""
        db.execute_update("""
            UPDATE alertas
            SET leida = 1, fecha_lectura = datetime('now')
            WHERE leida = 0
        """)
        log.info("Todas las alertas marcadas como leídas", categoria='alertas')
    
    @staticmethod
    def eliminar_alertas_antiguas(dias: int = 30):
        """Elimina alertas antiguas"""
        db.execute_update("""
            DELETE FROM alertas
            WHERE datetime(fecha_creacion) < datetime('now', '-' || ? || ' days')
        """, (dias,))
        log.info(f"Alertas de más de {dias} días eliminadas", categoria='alertas')
    
    # ===================================================================
    # CONFIGURACIÓN DE ALERTAS
    # ===================================================================
    
    @staticmethod
    def configurar_alerta(tipo_alerta: str, activa: bool, umbral: Optional[float] = None):
        """Configura una alerta específica"""
        db.execute_update("""
            UPDATE config_alertas
            SET activa = ?, umbral = ?
            WHERE tipo_alerta = ?
        """, (1 if activa else 0, umbral, tipo_alerta))
        
        log.info(f"Alerta '{tipo_alerta}' configurada: activa={activa}, umbral={umbral}", categoria='alertas')
    
    @staticmethod
    def obtener_configuracion():
        """Obtiene configuración de todas las alertas"""
        return db.execute_query("SELECT * FROM config_alertas ORDER BY tipo_alerta")


# ===================================================================
# INTERFAZ DE USUARIO
# ===================================================================

def menu_alertas():
    """Menú de gestión de alertas"""
    
    sistema = SistemaAlertas()
    
    while True:
        # Contar alertas no leídas
        num_no_leidas = sistema.contar_alertas_no_leidas()
        
        print("\n" + "="*70)
        print("SISTEMA DE ALERTAS")
        if num_no_leidas > 0:
            print(f"🔔 {num_no_leidas} alerta(s) no leída(s)")
        print("="*70)
        print("[1] Ver alertas no leídas")
        print("[2] Ver todas las alertas recientes")
        print("[3] Verificar alertas ahora")
        print("[4] Marcar todas como leídas")
        print("[5] Configurar alertas")
        print("[6] Limpiar alertas antiguas")
        print("[7] Volver")
        print("="*70)
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            ver_alertas_no_leidas(sistema)
        elif opcion == "2":
            ver_alertas_recientes(sistema)
        elif opcion == "3":
            verificar_alertas_interactivo(sistema)
        elif opcion == "4":
            marcar_todas_leidas_interactivo(sistema)
        elif opcion == "5":
            configurar_alertas_interactivo(sistema)
        elif opcion == "6":
            limpiar_alertas_interactivo(sistema)
        elif opcion == "7":
            break
        else:
            print("❌ Opción inválida")


def ver_alertas_no_leidas(sistema: SistemaAlertas):
    """Ver alertas no leídas"""
    
    alertas = sistema.obtener_alertas_no_leidas()
    
    print("\n" + "="*70)
    print("ALERTAS NO LEÍDAS")
    print("="*70)
    
    if not alertas:
        print("\n✅ No hay alertas pendientes")
    else:
        mostrar_lista_alertas(alertas, sistema)
        
        print("\n¿Marcar alertas como leídas?")
        print("[1] Marcar todas")
        print("[2] Marcar específicas")
        print("[3] No marcar")
        
        opcion = input("\nSelecciona: ").strip()
        
        if opcion == "1":
            sistema.marcar_todas_leidas()
            print("✅ Todas las alertas marcadas como leídas")
        elif opcion == "2":
            ids = input("IDs a marcar (separados por comas): ").strip()
            for id_str in ids.split(','):
                try:
                    sistema.marcar_leida(int(id_str.strip()))
                except ValueError:
                    pass
            print("✅ Alertas marcadas")
    
    input("\nPresiona Enter...")


def ver_alertas_recientes(sistema: SistemaAlertas):
    """Ver alertas recientes"""
    
    print("\n" + "="*70)
    print("ALERTAS RECIENTES (últimas 24 horas)")
    print("="*70)
    
    alertas = sistema.obtener_alertas_recientes()
    
    if not alertas:
        print("\n⚠️  No hay alertas en las últimas 24 horas")
    else:
        mostrar_lista_alertas(alertas, sistema)
    
    input("\nPresiona Enter...")


def verificar_alertas_interactivo(sistema: SistemaAlertas):
    """Verificar alertas manualmente"""
    
    print("\n🔍 Verificando alertas del ciclo activo...")
    
    sistema.verificar_todas()
    
    num_alertas = sistema.contar_alertas_no_leidas()
    
    if num_alertas > 0:
        print(f"\n⚠️  {num_alertas} alerta(s) nueva(s) detectada(s)")
        ver = input("¿Deseas verlas? (s/n): ").lower()
        if ver == 's':
            ver_alertas_no_leidas(sistema)
    else:
        print("\n✅ No se detectaron nuevas alertas")
        input("\nPresiona Enter...")


def marcar_todas_leidas_interactivo(sistema: SistemaAlertas):
    """Marcar todas como leídas"""
    
    num_alertas = sistema.contar_alertas_no_leidas()
    
    if num_alertas == 0:
        print("\n✅ No hay alertas pendientes")
    else:
        print(f"\n¿Marcar {num_alertas} alerta(s) como leídas?")
        confirmar = input("(s/n): ").lower()
        
        if confirmar == 's':
            sistema.marcar_todas_leidas()
            print("✅ Todas las alertas marcadas como leídas")
    
    input("\nPresiona Enter...")


def configurar_alertas_interactivo(sistema: SistemaAlertas):
    """Configurar alertas"""
    
    config = sistema.obtener_configuracion()
    
    print("\n" + "="*70)
    print("CONFIGURACIÓN DE ALERTAS")
    print("="*70)
    
    print("\nAlertas configuradas:\n")
    for i, alerta in enumerate(config, 1):
        estado = "✅ Activa" if alerta['activa'] else "❌ Inactiva"
        umbral = f"(Umbral: {alerta['umbral']})" if alerta['umbral'] else ""
        print(f"[{i}] {alerta['tipo_alerta'].replace('_', ' ').title()}")
        print(f"    Estado: {estado} {umbral}")
    
    print("\n" + "="*70)
    print("[1] Activar/Desactivar alerta")
    print("[2] Modificar umbral")
    print("[3] Volver")
    
    opcion = input("\nSelecciona: ").strip()
    
    if opcion == "1":
        try:
            idx = int(input("\nNúmero de alerta: ")) - 1
            if 0 <= idx < len(config):
                alerta = config[idx]
                nueva_activa = not alerta['activa']
                sistema.configurar_alerta(alerta['tipo_alerta'], nueva_activa, alerta['umbral'])
                print(f"✅ Alerta {'activada' if nueva_activa else 'desactivada'}")
        except ValueError:
            print("❌ Número inválido")
    
    elif opcion == "2":
        try:
            idx = int(input("\nNúmero de alerta: ")) - 1
            if 0 <= idx < len(config):
                alerta = config[idx]
                if alerta['umbral'] is not None:
                    print(f"Umbral actual: {alerta['umbral']}")
                    nuevo_umbral = float(input("Nuevo umbral: "))
                    sistema.configurar_alerta(alerta['tipo_alerta'], alerta['activa'], nuevo_umbral)
                    print("✅ Umbral actualizado")
                else:
                    print("⚠️  Esta alerta no tiene umbral configurable")
        except ValueError:
            print("❌ Valor inválido")
    
    input("\nPresiona Enter...")


def limpiar_alertas_interactivo(sistema: SistemaAlertas):
    """Limpiar alertas antiguas"""
    
    print("\n¿Eliminar alertas de más de cuántos días?")
    try:
        dias = int(input("Días (30): ") or "30")
        
        confirmar = input(f"\n¿Eliminar alertas de más de {dias} días? (s/n): ").lower()
        if confirmar == 's':
            sistema.eliminar_alertas_antiguas(dias)
            print("✅ Alertas antiguas eliminadas")
    except ValueError:
        print("❌ Valor inválido")
    
    input("\nPresiona Enter...")


def mostrar_lista_alertas(alertas, sistema: SistemaAlertas):
    """Muestra lista de alertas formateada"""
    
    for alerta in alertas:
        emoji = sistema.NIVELES.get(alerta['nivel'], '📝')
        leida = "✓" if alerta['leida'] else "●"
        
        print(f"\n{emoji} {leida} [{alerta['id']}] {alerta['titulo']}")
        print(f"   Nivel: {alerta['nivel'].title()}")
        print(f"   Fecha: {alerta['fecha_creacion']}")
        
        if alerta['referencia_tipo'] and alerta['referencia_id']:
            print(f"   Referencia: {alerta['referencia_tipo'].title()} #{alerta['referencia_id']}")
        
        print(f"   {alerta['mensaje']}")


# ===================================================================
# FUNCIÓN PARA MOSTRAR ALERTAS AL INICIO
# ===================================================================

def mostrar_banner_alertas():
    """Muestra banner de alertas al iniciar el sistema"""
    
    sistema = SistemaAlertas()
    
    # Verificar alertas
    sistema.verificar_todas()
    
    # Contar no leídas
    num_alertas = sistema.contar_alertas_no_leidas()
    
    if num_alertas > 0:
        print("\n" + "="*70)
        print(f"🔔 TIENES {num_alertas} ALERTA(S) PENDIENTE(S)")
        print("="*70)
        
        # Mostrar las 3 más importantes
        alertas = sistema.obtener_alertas_no_leidas(limite=3)
        
        for alerta in alertas:
            emoji = sistema.NIVELES.get(alerta['nivel'], '📝')
            print(f"\n{emoji} {alerta['titulo']}")
            print(f"   {alerta['mensaje']}")
        
        if num_alertas > 3:
            print(f"\n... y {num_alertas - 3} alerta(s) más")
        
        print("\n" + "="*70)
        print("Accede al menú de alertas para ver más detalles")
        print("="*70)


# ===================================================================
# EJECUCIÓN DIRECTA
# ===================================================================

if __name__ == "__main__":
    menu_alertas()
