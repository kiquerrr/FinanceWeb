"""
Rutas del Dashboard
Métricas, resúmenes y estadísticas generales
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db_manager import db

router = APIRouter()

# Modelos
class MetricaGeneral(BaseModel):
    titulo: str
    valor: float
    formato: str = "currency"
    cambio: Optional[float] = None
    trend: Optional[str] = None

class ResumenDia(BaseModel):
    fecha: date
    ventas_completadas: int
    capital_usado: float
    ganancia_generada: float
    comision_promedio: float

class ResumenGeneral(BaseModel):
    capital_total: float
    ganancia_total: float
    ciclos_completados: int
    ventas_hoy: int
    rendimiento_porcentual: float
    ultima_actualizacion: datetime

# Endpoints
@router.get("/resumen", response_model=ResumenGeneral)
async def get_resumen_general():
    """
    Obtener resumen general del sistema
    Incluye capital, ganancias, ciclos y métricas principales
    """
    try:
        with db.get_cursor(commit=False) as cursor:
            # Capital total de bóveda
            cursor.execute("""
                SELECT SUM(b.cantidad * b.precio_promedio) as capital_total
                FROM boveda_ciclo b
                JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo'
            """)
            capital = cursor.fetchone()['capital_total'] or 0.0
            
            # Ganancia total del ciclo activo
            cursor.execute("""
                SELECT ganancia_total, roi_total, id
                FROM ciclos WHERE estado = 'activo' LIMIT 1
            """)
            ciclo = cursor.fetchone()
            ganancia = ciclo['ganancia_total'] or 0.0 if ciclo else 0.0
            roi = ciclo['roi_total'] or 0.0 if ciclo else 0.0
            ciclo_id = ciclo['id'] if ciclo else None
            
            # Ciclos completados
            cursor.execute("SELECT COUNT(*) as total FROM ciclos WHERE estado = 'cerrado'")
            ciclos_completados = cursor.fetchone()['total']
            
            # Ventas de hoy
            ventas_hoy = 0
            if ciclo_id:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM ventas v
                    JOIN dias d ON v.dia_id = d.id
                    WHERE d.ciclo_id = ? AND DATE(v.fecha) = DATE('now')
                """, (ciclo_id,))
                ventas_hoy = cursor.fetchone()['total']
            
            return ResumenGeneral(
                capital_total=capital,
                ganancia_total=ganancia,
                ciclos_completados=ciclos_completados,
                ventas_hoy=ventas_hoy,
                rendimiento_porcentual=roi,
                ultima_actualizacion=datetime.now()
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/metricas", response_model=List[MetricaGeneral])
async def get_metricas_principales():
    """
    Obtener métricas principales en formato de tarjetas
    Para mostrar en el dashboard principal
    """
    try:
        with db.get_cursor(commit=False) as cursor:
            # Capital total
            cursor.execute("""
                SELECT SUM(b.cantidad * b.precio_promedio) as capital_total
                FROM boveda_ciclo b
                JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo'
            """)
            capital = cursor.fetchone()['capital_total'] or 0.0
            
            # Ganancia y ventas del ciclo activo
            cursor.execute("""
                SELECT ganancia_total, roi_total, id
                FROM ciclos WHERE estado = 'activo' LIMIT 1
            """)
            ciclo = cursor.fetchone()
            ganancia = ciclo['ganancia_total'] or 0.0 if ciclo else 0.0
            roi = ciclo['roi_total'] or 0.0 if ciclo else 0.0
            ciclo_id = ciclo['id'] if ciclo else None
            
            # Ventas de hoy
            ventas_hoy = 0
            if ciclo_id:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM ventas v
                    JOIN dias d ON v.dia_id = d.id
                    WHERE d.ciclo_id = ? AND DATE(v.fecha) = DATE('now')
                """, (ciclo_id,))
                ventas_hoy = cursor.fetchone()['total']
            
            return [
                MetricaGeneral(
                    titulo="Capital Total",
                    valor=capital,
                    formato="currency",
                    cambio=None,
                    trend="stable"
                ),
                MetricaGeneral(
                    titulo="Ganancia Total",
                    valor=ganancia,
                    formato="currency",
                    cambio=None,
                    trend="up" if ganancia > 0 else "stable"
                ),
                MetricaGeneral(
                    titulo="Rendimiento",
                    valor=roi,
                    formato="percentage",
                    cambio=None,
                    trend="up" if roi > 0 else "stable"
                ),
                MetricaGeneral(
                    titulo="Ventas Hoy",
                    valor=float(ventas_hoy),
                    formato="number",
                    cambio=None,
                    trend="stable"
                )
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/resumen-dia", response_model=ResumenDia)
async def get_resumen_dia_actual():
    """
    Obtener resumen del día operativo actual
    """
    # Por ahora devolver valores vacíos - conectar después con módulo dias
    return ResumenDia(
        fecha=date.today(),
        ventas_completadas=0,
        capital_usado=0.0,
        ganancia_generada=0.0,
        comision_promedio=0.0
    )

@router.get("/historial-dias", response_model=List[ResumenDia])
async def get_historial_dias(limite: int = 7):
    """
    Obtener historial de días operativos
    """
    return []

@router.get("/test")
async def test_dashboard():
    """Endpoint de prueba"""
    return {
        "message": "Módulo de dashboard funcionando",
        "timestamp": datetime.now().isoformat()
    }
