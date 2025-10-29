"""
Rutas de Operaciones
Gestión del día operativo y ventas
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
class IniciarDiaRequest(BaseModel):
    precio_compra: float = Field(..., gt=0)
    criptomoneda: str = Field(default="USDT")
    capital_inicial: Optional[float] = Field(None, gt=0)

class RegistrarVentaRequest(BaseModel):
    precio_venta: float = Field(..., gt=0)
    cantidad: float = Field(..., gt=0)
    comision: float = Field(..., ge=0, le=100)
    notas: Optional[str] = None

class DiaOperativo(BaseModel):
    id: int
    fecha: date
    estado: str
    precio_publicado: float
    criptomoneda: str
    ventas_realizadas: int
    capital_inicial: float
    ganancia_neta: float
    fecha_creacion: datetime

class Venta(BaseModel):
    id: int
    dia_id: int
    precio_venta: float
    cantidad: float
    comision: float
    ganancia: float
    fecha: datetime

@router.post("/iniciar-dia")
async def iniciar_dia_operativo(datos: IniciarDiaRequest):
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM ciclos WHERE estado = 'activo' LIMIT 1")
            ciclo = cursor.fetchone()
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            cursor.execute("SELECT id FROM dias WHERE ciclo_id = ? AND estado = 'abierto'", (ciclo['id'],))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Ya hay un día abierto")
            
            cursor.execute("SELECT id FROM criptomonedas WHERE simbolo = ?", (datos.criptomoneda,))
            cripto = cursor.fetchone()
            if not cripto:
                raise HTTPException(status_code=400, detail="Criptomoneda no encontrada")
            
            cursor.execute("SELECT COALESCE(MAX(numero_dia), 0) + 1 as siguiente FROM dias WHERE ciclo_id = ?", (ciclo['id'],))
            numero_dia = cursor.fetchone()['siguiente']
            
            fecha = datetime.now()
            cursor.execute("""
                INSERT INTO dias (ciclo_id, numero_dia, fecha, precio_publicado, cripto_operada_id, capital_inicial, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ciclo['id'], numero_dia, fecha, datos.precio_compra, cripto['id'], datos.capital_inicial or 0.0, 'abierto'))
            
            return {
                "success": True,
                "message": "Día operativo iniciado",
                "dia_id": cursor.lastrowid,
                "numero_dia": numero_dia,
                "fecha": fecha.date(),
                "precio_publicado": datos.precio_compra,
                "criptomoneda": datos.criptomoneda
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/registrar-venta")
async def registrar_venta(datos: RegistrarVentaRequest):
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT d.id, d.precio_publicado, d.ciclo_id, d.cripto_operada_id
                FROM dias d WHERE d.estado = 'abierto' LIMIT 1
            """)
            dia = cursor.fetchone()
            if not dia:
                raise HTTPException(status_code=400, detail="No hay día abierto")
            
            precio_compra = dia['precio_publicado']
            costo_total = datos.cantidad * precio_compra
            monto_venta = datos.cantidad * datos.precio_venta
            comision_monto = monto_venta * (datos.comision / 100)
            efectivo_recibido = monto_venta - comision_monto
            ganancia_bruta = monto_venta - costo_total
            ganancia_neta = efectivo_recibido - costo_total
            
            fecha = datetime.now()
            cursor.execute("""
                INSERT INTO ventas (dia_id, cripto_id, cantidad, precio_unitario, costo_total, 
                                   monto_venta, comision, efectivo_recibido, ganancia_bruta, 
                                   ganancia_neta, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dia['id'], dia['cripto_operada_id'], datos.cantidad, datos.precio_venta,
                  costo_total, monto_venta, comision_monto, efectivo_recibido,
                  ganancia_bruta, ganancia_neta, fecha))
            
            venta_id = cursor.lastrowid
            
            cursor.execute("""
                UPDATE dias SET ganancia_neta = COALESCE(ganancia_neta, 0) + ?,
                               ganancia_bruta = COALESCE(ganancia_bruta, 0) + ?
                WHERE id = ?
            """, (ganancia_neta, ganancia_bruta, dia['id']))
            
            cursor.execute("""
                UPDATE ciclos SET ganancia_total = COALESCE(ganancia_total, 0) + ? WHERE id = ?
            """, (ganancia_neta, dia['ciclo_id']))
            
            return {
                "success": True,
                "message": "Venta registrada",
                "venta_id": venta_id,
                "ganancia_neta": round(ganancia_neta, 2),
                "ganancia_bruta": round(ganancia_bruta, 2),
                "efectivo_recibido": round(efectivo_recibido, 2)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/dia-actual", response_model=DiaOperativo)
async def get_dia_actual():
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT d.id, d.fecha, d.estado, d.precio_publicado, d.capital_inicial, 
                       d.ganancia_neta, c.simbolo as cripto
                FROM dias d
                JOIN criptomonedas c ON d.cripto_operada_id = c.id
                WHERE d.estado = 'abierto' LIMIT 1
            """)
            dia = cursor.fetchone()
            if not dia:
                raise HTTPException(status_code=404, detail="No hay día abierto")
            
            cursor.execute("SELECT COUNT(*) as total FROM ventas WHERE dia_id = ?", (dia['id'],))
            ventas = cursor.fetchone()['total']
            
            return DiaOperativo(
                id=dia['id'],
                fecha=datetime.fromisoformat(str(dia['fecha'])).date(),
                estado=dia['estado'],
                precio_publicado=dia['precio_publicado'] or 0.0,
                criptomoneda=dia['cripto'],
                ventas_realizadas=ventas,
                capital_inicial=dia['capital_inicial'] or 0.0,
                ganancia_neta=dia['ganancia_neta'] or 0.0,
                fecha_creacion=datetime.fromisoformat(str(dia['fecha']))
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/cerrar-dia")
async def cerrar_dia_operativo():
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("SELECT id, ganancia_neta FROM dias WHERE estado = 'abierto' LIMIT 1")
            dia = cursor.fetchone()
            if not dia:
                raise HTTPException(status_code=400, detail="No hay día abierto")
            
            cursor.execute("SELECT COUNT(*) as total FROM ventas WHERE dia_id = ?", (dia['id'],))
            ventas = cursor.fetchone()['total']
            
            cursor.execute("UPDATE dias SET estado = 'cerrado', fecha_cierre = ? WHERE id = ?",
                         (datetime.now(), dia['id']))
            
            return {
                "success": True,
                "message": "Día cerrado",
                "ventas_totales": ventas,
                "ganancia_total": dia['ganancia_neta'] or 0.0
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/historial-ventas", response_model=List[Venta])
async def get_historial_ventas(dia_id: Optional[int] = None, limite: int = 20):
    try:
        with db.get_cursor(commit=False) as cursor:
            if dia_id:
                cursor.execute("""
                    SELECT id, dia_id, precio_unitario, cantidad, comision, ganancia_neta, fecha
                    FROM ventas WHERE dia_id = ? ORDER BY fecha DESC LIMIT ?
                """, (dia_id, limite))
            else:
                cursor.execute("""
                    SELECT id, dia_id, precio_unitario, cantidad, comision, ganancia_neta, fecha
                    FROM ventas ORDER BY fecha DESC LIMIT ?
                """, (limite,))
            
            return [Venta(
                id=r['id'], dia_id=r['dia_id'], precio_venta=r['precio_unitario'],
                cantidad=r['cantidad'], comision=r['comision'], ganancia=r['ganancia_neta'],
                fecha=datetime.fromisoformat(str(r['fecha']))
            ) for r in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/test")
async def test_operaciones():
    return {"message": "Operaciones funcionando", "timestamp": datetime.now().isoformat()}
