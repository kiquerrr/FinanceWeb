"""
Rutas de Ciclos
Gestión de ciclos de operación
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db_manager import db

router = APIRouter()

# Modelos
class Ciclo(BaseModel):
    id: int
    numero: int
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    capital_inicial: float
    capital_final: Optional[float] = None
    ganancia_total: Optional[float] = None
    rendimiento_porcentual: Optional[float] = None
    dias_operados: int
    ventas_totales: int
    estado: str

class IniciarCicloRequest(BaseModel):
    capital_inicial: Optional[float] = Field(None, ge=0)
    meta_ganancia: Optional[float] = Field(None, gt=0)

class FinalizarCicloRequest(BaseModel):
    notas: Optional[str] = None

class EstadisticasCiclo(BaseModel):
    promedio_ganancia_diaria: float
    mejor_dia: Optional[date] = None
    mejor_dia_ganancia: Optional[float] = None
    peor_dia: Optional[date] = None
    peor_dia_ganancia: Optional[float] = None
    dias_con_operaciones: int
    dias_sin_operaciones: int
    total_ventas: int

# Endpoints
@router.get("/activo", response_model=Ciclo)
async def get_ciclo_activo():
    """Obtener información del ciclo activo actual"""
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, fecha_inicio, inversion_inicial, dias_operados, 
                       ganancia_total, roi_total, estado
                FROM ciclos WHERE estado = 'activo' LIMIT 1
            """)
            ciclo = cursor.fetchone()
            
            if not ciclo:
                raise HTTPException(status_code=404, detail="No hay ciclo activo")
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM ventas v
                JOIN dias d ON v.dia_id = d.id WHERE d.ciclo_id = ?
            """, (ciclo['id'],))
            ventas = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) FROM ciclos WHERE id <= ?", (ciclo['id'],))
            numero_ciclo = cursor.fetchone()[0]
            
            return Ciclo(
                id=ciclo['id'],
                numero=numero_ciclo,
                fecha_inicio=datetime.fromisoformat(str(ciclo['fecha_inicio'])).date(),
                fecha_fin=None,
                capital_inicial=ciclo['inversion_inicial'] or 0.0,
                capital_final=None,
                ganancia_total=ciclo['ganancia_total'] or 0.0,
                rendimiento_porcentual=ciclo['roi_total'],
                dias_operados=ciclo['dias_operados'] or 0,
                ventas_totales=ventas,
                estado=ciclo['estado']
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/historial", response_model=List[Ciclo])
async def get_historial_ciclos(limite: int = 10):
    """Obtener historial de ciclos finalizados"""
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, fecha_inicio, fecha_cierre, dias_operados,
                       inversion_inicial, capital_final, ganancia_total, roi_total, estado
                FROM ciclos
                WHERE estado = 'cerrado'
                ORDER BY fecha_inicio DESC
                LIMIT ?
            """, (limite,))
            
            ciclos = []
            for row in cursor.fetchall():
                cursor.execute("""
                    SELECT COUNT(*) as total FROM ventas v
                    JOIN dias d ON v.dia_id = d.id WHERE d.ciclo_id = ?
                """, (row['id'],))
                ventas = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) FROM ciclos WHERE id <= ?", (row['id'],))
                numero = cursor.fetchone()[0]
                
                ciclos.append(Ciclo(
                    id=row['id'],
                    numero=numero,
                    fecha_inicio=datetime.fromisoformat(str(row['fecha_inicio'])).date(),
                    fecha_fin=datetime.fromisoformat(str(row['fecha_cierre'])).date() if row['fecha_cierre'] else None,
                    capital_inicial=row['inversion_inicial'] or 0.0,
                    capital_final=row['capital_final'],
                    ganancia_total=row['ganancia_total'],
                    rendimiento_porcentual=row['roi_total'],
                    dias_operados=row['dias_operados'] or 0,
                    ventas_totales=ventas,
                    estado=row['estado']
                ))
            
            return ciclos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{ciclo_id}", response_model=Ciclo)
async def get_ciclo_por_id(ciclo_id: int):
    """Obtener información de un ciclo específico por ID"""
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, fecha_inicio, fecha_cierre, dias_operados,
                       inversion_inicial, capital_final, ganancia_total, roi_total, estado
                FROM ciclos WHERE id = ?
            """, (ciclo_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Ciclo no encontrado")
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM ventas v
                JOIN dias d ON v.dia_id = d.id WHERE d.ciclo_id = ?
            """, (row['id'],))
            ventas = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) FROM ciclos WHERE id <= ?", (row['id'],))
            numero = cursor.fetchone()[0]
            
            return Ciclo(
                id=row['id'],
                numero=numero,
                fecha_inicio=datetime.fromisoformat(str(row['fecha_inicio'])).date(),
                fecha_fin=datetime.fromisoformat(str(row['fecha_cierre'])).date() if row['fecha_cierre'] else None,
                capital_inicial=row['inversion_inicial'] or 0.0,
                capital_final=row['capital_final'],
                ganancia_total=row['ganancia_total'],
                rendimiento_porcentual=row['roi_total'],
                dias_operados=row['dias_operados'] or 0,
                ventas_totales=ventas,
                estado=row['estado']
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{ciclo_id}/estadisticas", response_model=EstadisticasCiclo)
async def get_estadisticas_ciclo(ciclo_id: int):
    """Obtener estadísticas detalladas de un ciclo"""
    try:
        with db.get_cursor(commit=False) as cursor:
            # Verificar que el ciclo existe
            cursor.execute("SELECT id FROM ciclos WHERE id = ?", (ciclo_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ciclo no encontrado")
            
            # Total de ventas
            cursor.execute("""
                SELECT COUNT(*) as total FROM ventas v
                JOIN dias d ON v.dia_id = d.id WHERE d.ciclo_id = ?
            """, (ciclo_id,))
            total_ventas = cursor.fetchone()['total']
            
            # Días con operaciones
            cursor.execute("""
                SELECT COUNT(DISTINCT d.id) as total FROM dias d
                WHERE d.ciclo_id = ? AND d.estado = 'cerrado'
            """, (ciclo_id,))
            dias_operados = cursor.fetchone()['total']
            
            # Promedio de ganancia diaria
            cursor.execute("""
                SELECT AVG(ganancia_neta) as promedio FROM dias
                WHERE ciclo_id = ? AND estado = 'cerrado' AND ganancia_neta IS NOT NULL
            """, (ciclo_id,))
            promedio = cursor.fetchone()['promedio'] or 0.0
            
            # Mejor día
            cursor.execute("""
                SELECT fecha, ganancia_neta FROM dias
                WHERE ciclo_id = ? AND estado = 'cerrado' AND ganancia_neta IS NOT NULL
                ORDER BY ganancia_neta DESC LIMIT 1
            """, (ciclo_id,))
            mejor = cursor.fetchone()
            
            # Peor día
            cursor.execute("""
                SELECT fecha, ganancia_neta FROM dias
                WHERE ciclo_id = ? AND estado = 'cerrado' AND ganancia_neta IS NOT NULL
                ORDER BY ganancia_neta ASC LIMIT 1
            """, (ciclo_id,))
            peor = cursor.fetchone()
            
            return EstadisticasCiclo(
                promedio_ganancia_diaria=round(promedio, 2),
                mejor_dia=datetime.fromisoformat(str(mejor['fecha'])).date() if mejor else None,
                mejor_dia_ganancia=mejor['ganancia_neta'] if mejor else None,
                peor_dia=datetime.fromisoformat(str(peor['fecha'])).date() if peor else None,
                peor_dia_ganancia=peor['ganancia_neta'] if peor else None,
                dias_con_operaciones=dias_operados,
                dias_sin_operaciones=0,
                total_ventas=total_ventas
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/iniciar")
async def iniciar_nuevo_ciclo(datos: IniciarCicloRequest):
    """Iniciar un nuevo ciclo de operaciones"""
    try:
        with db.get_cursor(commit=True) as cursor:
            # Verificar que no hay ciclo activo
            cursor.execute("SELECT id FROM ciclos WHERE estado = 'activo'")
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Ya existe un ciclo activo")
            
            # Calcular capital inicial desde bóveda si no se proporciona
            if datos.capital_inicial is None or datos.capital_inicial == 0:
                # Buscar el último ciclo cerrado para obtener su bóveda
                cursor.execute("""
                    SELECT SUM(cantidad * precio_promedio) as capital_boveda
                    FROM boveda_ciclo b
                    JOIN ciclos c ON b.ciclo_id = c.id
                    WHERE c.estado = 'cerrado'
                    ORDER BY c.id DESC LIMIT 1
                """)
                boveda_anterior = cursor.fetchone()
                capital_inicial = boveda_anterior['capital_boveda'] if boveda_anterior and boveda_anterior['capital_boveda'] else 0
            else:
                capital_inicial = datos.capital_inicial
            
            # Crear nuevo ciclo
            fecha = datetime.now()
            cursor.execute("""
                INSERT INTO ciclos (fecha_inicio, inversion_inicial, estado, dias_planificados, fecha_fin_estimada)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha, capital_inicial, 'activo', 30, fecha.date()))
            
            ciclo_id = cursor.lastrowid
            
            cursor.execute("SELECT COUNT(*) FROM ciclos WHERE id <= ?", (ciclo_id,))
            numero = cursor.fetchone()[0]
            
            return {
                "success": True,
                "message": "Ciclo iniciado correctamente",
                "ciclo_id": ciclo_id,
                "numero": numero,
                "capital_inicial": capital_inicial,
                "fecha_inicio": str(fecha.date())
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/finalizar")
async def finalizar_ciclo_actual(datos: FinalizarCicloRequest):
    """Finalizar el ciclo activo actual"""
    try:
        with db.get_cursor(commit=True) as cursor:
            # Buscar ciclo activo
            cursor.execute("""
                SELECT id, inversion_inicial, ganancia_total FROM ciclos 
                WHERE estado = 'activo' LIMIT 1
            """)
            ciclo = cursor.fetchone()
            
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            # Calcular capital final y ROI
            capital_final = ciclo['inversion_inicial'] + (ciclo['ganancia_total'] or 0)
            roi = ((ciclo['ganancia_total'] or 0) / ciclo['inversion_inicial'] * 100) if ciclo['inversion_inicial'] > 0 else 0
            
            # Cerrar ciclo
            cursor.execute("""
                UPDATE ciclos SET
                    estado = 'cerrado',
                    fecha_cierre = ?,
                    capital_final = ?,
                    roi_total = ?
                WHERE id = ?
            """, (datetime.now(), capital_final, roi, ciclo['id']))
            
            return {
                "success": True,
                "message": "Ciclo finalizado correctamente",
                "capital_final": round(capital_final, 2),
                "ganancia_total": round(ciclo['ganancia_total'] or 0, 2),
                "rendimiento_porcentual": round(roi, 2),
                "notas": datos.notas
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/test")
async def test_ciclos():
    return {"message": "Ciclos funcionando", "timestamp": datetime.now().isoformat()}

class TransferirCapitalRequest(BaseModel):
    cripto_id: int = Field(..., description="ID de la criptomoneda a transferir")
    cantidad: float = Field(..., gt=0, description="Cantidad a transferir (0 = todo)")
    transferir_todo: bool = Field(False, description="Transferir toda la cantidad disponible")

@router.post("/transferir-capital")
async def transferir_capital_a_ciclo(datos: TransferirCapitalRequest):
    """Transfiere capital de la bóveda al ciclo activo"""
    try:
        with db.get_cursor(commit=True) as cursor:
            # Verificar ciclo activo
            cursor.execute("SELECT id, inversion_inicial FROM ciclos WHERE estado = 'activo' LIMIT 1")
            ciclo = cursor.fetchone()
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            ciclo_id = ciclo['id']
            
            # Verificar que la cripto existe en bóveda
            cursor.execute("""
                SELECT b.cantidad, b.precio_promedio, c.nombre, c.simbolo
                FROM boveda_ciclo b
                JOIN criptomonedas c ON b.cripto_id = c.id
                WHERE b.ciclo_id = ? AND b.cripto_id = ?
            """, (ciclo_id, datos.cripto_id))
            
            boveda = cursor.fetchone()
            if not boveda:
                raise HTTPException(status_code=404, detail="Criptomoneda no encontrada en bóveda")
            
            # Determinar cantidad a transferir
            cantidad_transferir = boveda['cantidad'] if datos.transferir_todo else datos.cantidad
            
            if cantidad_transferir > boveda['cantidad']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cantidad insuficiente. Disponible: {boveda['cantidad']}"
                )
            
            # Calcular valor en USD
            valor_usd = cantidad_transferir * boveda['precio_promedio']
            
            # Actualizar capital del ciclo
            nuevo_capital = ciclo['inversion_inicial'] + valor_usd
            cursor.execute("""
                UPDATE ciclos SET inversion_inicial = ? WHERE id = ?
            """, (nuevo_capital, ciclo_id))
            
            return {
                "success": True,
                "message": f"Transferido {cantidad_transferir} {boveda['simbolo']} al ciclo",
                "cripto": boveda['simbolo'],
                "cantidad_transferida": cantidad_transferir,
                "valor_usd": round(valor_usd, 2),
                "nuevo_capital_ciclo": round(nuevo_capital, 2)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
