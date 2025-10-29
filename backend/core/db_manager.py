# -*- coding: utf-8 -*-
"""
=============================================================================
GESTOR DE BASE DE DATOS v3.0
=============================================================================
Gestor centralizado y seguro de conexiones a SQLite
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any


# ===================================================================
# CONFIGURACIÓN
# ===================================================================

DB_FILE = 'data/arbitraje.db'


# ===================================================================
# CLASE DATABASE MANAGER
# ===================================================================

class DatabaseManager:
    """Gestor centralizado de conexiones a la base de datos"""
    
    def __init__(self):
        """Inicializa el gestor"""
        self.db_path = Path(DB_FILE)
        self._verificar_bd_existe()
    
    def _verificar_bd_existe(self):
        """Verifica que la base de datos existe"""
        if not self.db_path.exists():
            # Crear directorio data si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            raise FileNotFoundError(
                f"Base de datos no encontrada: {self.db_path}\n"
                "Ejecuta inicializar_bd.py primero"
            )
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        Context manager para obtener cursor de BD
        
        Args:
            commit: Si True, hace commit automático al salir
        
        Yields:
            sqlite3.Cursor: Cursor de la base de datos
        
        Example:
            with db.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO ...")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        
        cursor = conn.cursor()
        
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = (), 
                     fetch_one: bool = False) -> Optional[List[Dict]]:
        """
        Ejecuta una consulta SELECT y retorna resultados
        
        Args:
            query: Query SQL
            params: Parámetros de la query
            fetch_one: Si True, retorna solo un resultado
        
        Returns:
            Lista de diccionarios o un diccionario (si fetch_one=True)
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                rows = cursor.fetchall()
                return [dict(row) for row in rows] if rows else []
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Ejecuta una consulta INSERT/UPDATE/DELETE
        
        Args:
            query: Query SQL
            params: Parámetros de la query
        
        Returns:
            ID del último registro insertado (para INSERT) o número de filas afectadas
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            
            # Para INSERT, retornar lastrowid
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            # Para UPDATE/DELETE, retornar rowcount
            else:
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Ejecuta múltiples operaciones INSERT/UPDATE
        
        Args:
            query: Query SQL
            params_list: Lista de tuplas con parámetros
        
        Returns:
            Número de filas afectadas
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount


# ===================================================================
# FUNCIONES DE UTILIDAD
# ===================================================================

def verificar_conexion() -> bool:
    """
    Verifica que la conexión a la BD funciona
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        db_test = DatabaseManager()
        with db_test.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        return False


# ===================================================================
# INSTANCIA GLOBAL
# ===================================================================

db = DatabaseManager()