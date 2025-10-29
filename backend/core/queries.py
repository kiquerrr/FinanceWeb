# -*- coding: utf-8 -*-
"""
=============================================================================
MÓDULO DE QUERIES
=============================================================================
Queries SQL reutilizables para evitar duplicación
Todas las queries comunes en un solo lugar
"""

from core.db_manager import db


class Queries:
    """Queries SQL centralizadas"""
    
    # ===================================================================
    # CONFIGURACIÓN
    # ===================================================================
    
    @staticmethod
    def obtener_config():
        """Obtiene la configuración completa del sistema"""
        return db.execute_query(
            "SELECT * FROM config WHERE id = 1",
            fetch_one=True
        )
    
    @staticmethod
    def obtener_comision():
        """Obtiene solo la comisión"""
        config = Queries.obtener_config()
        return config['comision_default'] if config else 0.35
    
    @staticmethod
    def obtener_ganancia_objetivo():
        """Obtiene solo la ganancia objetivo"""
        config = Queries.obtener_config()
        return config['ganancia_neta_default'] if config else 2.0
    
    @staticmethod
    def obtener_limites_ventas():
        """Obtiene límites de ventas"""
        config = Queries.obtener_config()
        if config:
            return config['limite_ventas_min'], config['limite_ventas_max']
        return 3, 5
    
    # ===================================================================
    # CICLOS
    # ===================================================================
    
    @staticmethod
    def obtener_ciclo_activo():
        """Obtiene el ciclo activo"""
        return db.execute_query("""
            SELECT * FROM ciclos
            WHERE estado = 'activo'
            ORDER BY id DESC
            LIMIT 1
        """, fetch_one=True)
    
    @staticmethod
    def obtener_ciclo_por_id(ciclo_id: int):
        """Obtiene un ciclo por ID"""
        return db.execute_query(
            "SELECT * FROM ciclos WHERE id = ?",
            (ciclo_id,),
            fetch_one=True
        )
    
    @staticmethod
    def contar_ciclos():
        """Cuenta total de ciclos"""
        resultado = db.execute_query(
            "SELECT COUNT(*) as total FROM ciclos",
            fetch_one=True
        )
        return resultado['total']
    
    @staticmethod
    def listar_ciclos(limite: int = 10):
        """Lista últimos ciclos"""
        return db.execute_query("""
            SELECT * FROM ciclos
            ORDER BY id DESC
            LIMIT ?
        """, (limite,))
    
    # ===================================================================
    # DÍAS
    # ===================================================================
    
    @staticmethod
    def obtener_dia_por_id(dia_id: int):
        """Obtiene un día por ID"""
        return db.execute_query(
            "SELECT * FROM dias WHERE id = ?",
            (dia_id,),
            fetch_one=True
        )
    
    @staticmethod
    def obtener_dia_abierto(ciclo_id: int):
        """Obtiene día abierto del ciclo"""
        return db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ? AND estado = 'abierto'
            ORDER BY numero_dia DESC
            LIMIT 1
        """, (ciclo_id,), fetch_one=True)
    
    @staticmethod
    def contar_dias_ciclo(ciclo_id: int):
        """Cuenta días de un ciclo"""
        resultado = db.execute_query("""
            SELECT COUNT(*) as total
            FROM dias
            WHERE ciclo_id = ?
        """, (ciclo_id,), fetch_one=True)
        return resultado['total']
    
    @staticmethod
    def obtener_ultimo_dia_cerrado(ciclo_id: int):
        """Obtiene último día cerrado"""
        return db.execute_query("""
            SELECT * FROM dias
            WHERE ciclo_id = ? AND estado = 'cerrado'
            ORDER BY numero_dia DESC
            LIMIT 1
        """, (ciclo_id,), fetch_one=True)
    
    # ===================================================================
    # VENTAS
    # ===================================================================
    
    @staticmethod
    def contar_ventas_dia(dia_id: int):
        """Cuenta ventas de un día"""
        resultado = db.execute_query(
            "SELECT COUNT(*) as total FROM ventas WHERE dia_id = ?",
            (dia_id,),
            fetch_one=True
        )
        return resultado['total']
    
    @staticmethod
    def obtener_ventas_dia(dia_id: int):
        """Obtiene todas las ventas de un día"""
        return db.execute_query("""
            SELECT v.*, c.nombre, c.simbolo
            FROM ventas v
            JOIN criptomonedas c ON v.cripto_id = c.id
            WHERE v.dia_id = ?
            ORDER BY v.fecha
        """, (dia_id,))
    
    @staticmethod
    def calcular_totales_ventas_dia(dia_id: int):
        """Calcula totales de ventas de un día"""
        return db.execute_query("""
            SELECT 
                COUNT(*) as num_ventas,
                COALESCE(SUM(cantidad), 0) as cantidad_total,
                COALESCE(SUM(monto_venta), 0) as monto_total,
                COALESCE(SUM(comision), 0) as comisiones_total,
                COALESCE(SUM(ganancia_neta), 0) as ganancia_total
            FROM ventas
            WHERE dia_id = ?
        """, (dia_id,), fetch_one=True)
    
    # ===================================================================
    # BÓVEDA
    # ===================================================================
    
    @staticmethod
    def obtener_capital_boveda(ciclo_id: int):
        """Obtiene capital total en bóveda del ciclo"""
        resultado = db.execute_query("""
            SELECT COALESCE(SUM(cantidad * precio_promedio), 0) as capital
            FROM boveda_ciclo
            WHERE ciclo_id = ?
        """, (ciclo_id,), fetch_one=True)
        return resultado['capital']
    
    @staticmethod
    def obtener_criptos_boveda(ciclo_id: int):
        """Obtiene todas las criptos en bóveda"""
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
            ORDER BY valor_usd DESC
        """, (ciclo_id,))
    
    @staticmethod
    def obtener_cantidad_cripto(ciclo_id: int, cripto_id: int):
        """Obtiene cantidad disponible de una cripto"""
        resultado = db.execute_query("""
            SELECT cantidad
            FROM boveda_ciclo
            WHERE ciclo_id = ? AND cripto_id = ?
        """, (ciclo_id, cripto_id), fetch_one=True)
        return resultado['cantidad'] if resultado else 0
    
    @staticmethod
    def obtener_precio_promedio_cripto(ciclo_id: int, cripto_id: int):
        """Obtiene precio promedio de una cripto"""
        resultado = db.execute_query("""
            SELECT precio_promedio
            FROM boveda_ciclo
            WHERE ciclo_id = ? AND cripto_id = ?
        """, (ciclo_id, cripto_id), fetch_one=True)
        return resultado['precio_promedio'] if resultado else 0
    
    # ===================================================================
    # CRIPTOMONEDAS
    # ===================================================================
    
    @staticmethod
    def listar_criptomonedas():
        """Lista todas las criptomonedas"""
        return db.execute_query("""
            SELECT * FROM criptomonedas
            ORDER BY tipo, nombre
        """)
    
    @staticmethod
    def obtener_cripto_por_id(cripto_id: int):
        """Obtiene una criptomoneda por ID"""
        return db.execute_query(
            "SELECT * FROM criptomonedas WHERE id = ?",
            (cripto_id,),
            fetch_one=True
        )
    
    @staticmethod
    def obtener_cripto_por_simbolo(simbolo: str):
        """Obtiene una criptomoneda por símbolo"""
        return db.execute_query(
            "SELECT * FROM criptomonedas WHERE simbolo = ?",
            (simbolo.upper(),),
            fetch_one=True
        )
    
    # ===================================================================
    # ESTADÍSTICAS
    # ===================================================================
    
    @staticmethod
    def obtener_estadisticas_generales():
        """Obtiene estadísticas generales del sistema"""
        with db.get_cursor(commit=False) as cursor:
            stats = {}
            
            # Ciclos
            cursor.execute("SELECT COUNT(*) as total FROM ciclos")
            stats['total_ciclos'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM ciclos WHERE estado='activo'")
            stats['ciclos_activos'] = cursor.fetchone()['total']
            
            # Días
            cursor.execute("SELECT COUNT(*) as total FROM dias WHERE estado='cerrado'")
            stats['dias_operados'] = cursor.fetchone()['total']
            
            # Ventas
            cursor.execute("SELECT COUNT(*) as total FROM ventas")
            stats['total_ventas'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COALESCE(SUM(ganancia_neta), 0) as total FROM ventas")
            stats['ganancia_total'] = cursor.fetchone()['total']
            
            # Compras
            cursor.execute("SELECT COUNT(*) as total FROM compras")
            stats['total_compras'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COALESCE(SUM(monto_usd), 0) as total FROM compras")
            stats['capital_invertido'] = cursor.fetchone()['total']
            
            return stats
    
    # ===================================================================
    # EFECTIVO
    # ===================================================================
    
    @staticmethod
    def obtener_efectivo_total(ciclo_id: int):
        """Obtiene efectivo total acumulado en el ciclo"""
        resultado = db.execute_query("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM efectivo_banco
            WHERE ciclo_id = ?
        """, (ciclo_id,), fetch_one=True)
        return resultado['total']
    
    @staticmethod
    def obtener_efectivo_dia(dia_id: int):
        """Obtiene efectivo del día"""
        resultado = db.execute_query("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM efectivo_banco
            WHERE dia_id = ?
        """, (dia_id,), fetch_one=True)
        return resultado['total']


# ===================================================================
# INSTANCIA GLOBAL
# ===================================================================

queries = Queries()


# ===================================================================
# TESTING
# ===================================================================

if __name__ == "__main__":
    print("="*60)
    print("TEST DE QUERIES")
    print("="*60)
    
    # Test config
    print("\n[Test 1] Configuración:")
    config = queries.obtener_config()
    if config:
        print(f"   ✅ Comisión: {config['comision_default']}%")
        print(f"   ✅ Ganancia objetivo: {config['ganancia_neta_default']}%")
    
    # Test ciclo activo
    print("\n[Test 2] Ciclo activo:")
    ciclo = queries.obtener_ciclo_activo()
    if ciclo:
        print(f"   ✅ Ciclo #{ciclo['id']} activo")
    else:
        print("   ⚠️  No hay ciclo activo")
    
    # Test estadísticas
    print("\n[Test 3] Estadísticas:")
    stats = queries.obtener_estadisticas_generales()
    print(f"   ✅ Ciclos: {stats['total_ciclos']}")
    print(f"   ✅ Días operados: {stats['dias_operados']}")
    print(f"   ✅ Ventas: {stats['total_ventas']}")
    print(f"   ✅ Ganancia total: ${stats['ganancia_total']:.2f}")
    
    # Test criptomonedas
    print("\n[Test 4] Criptomonedas:")
    criptos = queries.listar_criptomonedas()
    print(f"   ✅ {len(criptos)} criptomonedas disponibles")
    for cripto in criptos[:3]:
        print(f"      • {cripto['nombre']} ({cripto['simbolo']})")
    
    print("\n" + "="*60)
