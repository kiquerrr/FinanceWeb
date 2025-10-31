"""
Rutas de Operaciones Diarias
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db_manager import db
from core.calculos import calc

router = APIRouter()

class IniciarDiaRequest(BaseModel):
    cripto_id: int
    capital_usd: float = Field(..., gt=0, description="Capital en USD a invertir")
    tasa_compra: float = Field(..., gt=0, description="Tasa de compra (USD por cripto)")
    ganancia_objetivo_pct: Optional[float] = Field(2.0, description="% de ganancia objetivo")
    comision_pct: Optional[float] = Field(0.35, description="% de comisión")

class RegistrarVentaRequest(BaseModel):
    cantidad: float = Field(..., gt=0)
    precio_venta: float = Field(..., gt=0)

class DiaOperativo(BaseModel):
    id: int
    numero_dia: int
    ciclo_id: int
    cripto_id: int
    cripto_nombre: str
    cripto_simbolo: str
    capital_usd: float
    cantidad_cripto: float
    tasa_compra: float
    precio_objetivo: float
    precio_equilibrio: float
    ganancia_neta: float
    ventas_realizadas: int
    estado: str
    fecha: str

class Venta(BaseModel):
    id: int
    cantidad: float
    precio_venta: float
    monto_bruto: float
    comision: float
    monto_neto: float
    ganancia: float
    fecha: str

@router.post("/iniciar-dia")
async def iniciar_dia(datos: IniciarDiaRequest):
    """Inicia un nuevo día de operación"""
    try:
        with db.get_cursor(commit=True) as cursor:
            # Verificar ciclo activo
            cursor.execute("SELECT id FROM ciclos WHERE estado = 'activo' LIMIT 1")
            ciclo = cursor.fetchone()
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            ciclo_id = ciclo['id']
            
            # Verificar que no hay día abierto
            cursor.execute("""
                SELECT id FROM dias WHERE ciclo_id = ? AND estado = 'abierto'
            """, (ciclo_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Ya hay un día abierto")
            
            # Verificar cripto
            cursor.execute("SELECT id, nombre, simbolo FROM criptomonedas WHERE id = ?", (datos.cripto_id,))
            cripto = cursor.fetchone()
            if not cripto:
                raise HTTPException(status_code=404, detail="Criptomoneda no encontrada")
            
            # CALCULAR CANTIDAD DE CRIPTO
            cantidad_cripto = datos.capital_usd / datos.tasa_compra
            
            # CALCULAR PRECIO OBJETIVO (para ganancia del 2%)
            # Meta en USD = capital * 1.02
            meta_usd = datos.capital_usd * (1 + datos.ganancia_objetivo_pct / 100)
            
            # Monto bruto antes de comisión
            monto_bruto = meta_usd / (1 - datos.comision_pct / 100)
            
            # Precio objetivo por cripto
            precio_objetivo = monto_bruto / cantidad_cripto
            
            # CALCULAR PUNTO DE EQUILIBRIO
            # Para recuperar exactamente el capital invertido
            equilibrio_bruto = datos.capital_usd / (1 - datos.comision_pct / 100)
            precio_equilibrio = equilibrio_bruto / cantidad_cripto
            
            # Calcular número de día
            cursor.execute("""
                SELECT COALESCE(MAX(numero_dia), 0) + 1 as siguiente
                FROM dias WHERE ciclo_id = ?
            """, (ciclo_id,))
            numero_dia = cursor.fetchone()['siguiente']
            
            # Insertar día
            cursor.execute("""
                INSERT INTO dias (
                    ciclo_id, numero_dia, cripto_operada_id,
                    capital_inicial, cantidad_cripto, tasa_compra,
                    precio_publicado, precio_equilibrio,
                    estado, fecha
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'abierto', datetime('now'))
            """, (
                ciclo_id, numero_dia, datos.cripto_id,
                datos.capital_usd, cantidad_cripto, datos.tasa_compra,
                precio_objetivo, precio_equilibrio
            ))
            
            dia_id = cursor.lastrowid
            
            return {
                "success": True,
                "message": f"Día #{numero_dia} iniciado",
                "dia_id": dia_id,
                "numero_dia": numero_dia,
                "cripto": cripto['nombre'],
                "capital_usd": datos.capital_usd,
                "cantidad_cripto": cantidad_cripto,
                "tasa_compra": datos.tasa_compra,
                "precio_objetivo": round(precio_objetivo, 8),
                "precio_equilibrio": round(precio_equilibrio, 8),
                "ganancia_esperada": round(meta_usd - datos.capital_usd, 2)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/dia-actual")
async def get_dia_actual():
    """Obtiene el día operativo actual"""
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT d.*, c.nombre as cripto_nombre, c.simbolo as cripto_simbolo
                FROM dias d
                JOIN criptomonedas c ON d.cripto_operada_id = c.id
                WHERE d.estado = 'abierto'
                ORDER BY d.id DESC LIMIT 1
            """)
            dia = cursor.fetchone()
            
            if not dia:
                raise HTTPException(status_code=404, detail="No hay día activo")
            
            # Contar ventas
            cursor.execute("SELECT COUNT(*) as total FROM ventas WHERE dia_id = ?", (dia['id'],))
            ventas_count = cursor.fetchone()['total']
            
            # Calcular ganancia acumulada
            cursor.execute("""
                SELECT COALESCE(SUM(ganancia_neta), 0) as ganancia
                FROM ventas WHERE dia_id = ?
            """, (dia['id'],))
            ganancia = cursor.fetchone()['ganancia']
            
            return DiaOperativo(
                id=dia['id'],
                numero_dia=dia['numero_dia'],
                ciclo_id=dia['ciclo_id'],
                cripto_id=dia['cripto_operada_id'],
                cripto_nombre=dia['cripto_nombre'],
                cripto_simbolo=dia['cripto_simbolo'],
                capital_usd=dia['capital_inicial'],
                cantidad_cripto=dia['cantidad_cripto'],
                tasa_compra=dia['tasa_compra'],
                precio_objetivo=dia['precio_publicado'],
                precio_equilibrio=dia['precio_equilibrio'],
                ganancia_neta=ganancia,
                ventas_realizadas=ventas_count,
                estado=dia['estado'],
                fecha=dia['fecha']
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/registrar-venta")
async def registrar_venta(datos: RegistrarVentaRequest):
    """Registra una venta del día actual"""
    try:
        with db.get_cursor(commit=True) as cursor:
            # Obtener día actual
            cursor.execute("""
                SELECT d.*, cy.id as ciclo_id
                FROM dias d
                JOIN ciclos cy ON d.ciclo_id = cy.id
                WHERE d.estado = 'abierto' AND cy.estado = 'activo'
                ORDER BY d.id DESC LIMIT 1
            """)
            dia = cursor.fetchone()
            
            if not dia:
                raise HTTPException(status_code=404, detail="No hay día activo")
            
            # Obtener comisión de config
            cursor.execute("SELECT comision_default FROM config WHERE id = 1")
            config = cursor.fetchone()
            comision_pct = config['comision_default'] if config else 0.35
            
            # CALCULAR VENTA
            monto_bruto = datos.cantidad * datos.precio_venta
            comision = monto_bruto * (comision_pct / 100)
            monto_neto = monto_bruto - comision
            
            # Calcular costo de lo vendido
            costo = datos.cantidad * dia['tasa_compra']
            
            # Ganancia
            ganancia = monto_neto - costo
            
            # Insertar venta
            cursor.execute("""
                INSERT INTO ventas (
                    dia_id, cripto_id, cantidad, precio_unitario,
                    costo_total, monto_venta, comision, efectivo_recibido,
                    ganancia_bruta, ganancia_neta, fecha
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                dia['id'], dia['cripto_operada_id'], datos.cantidad, datos.precio_venta,
                costo, monto_bruto, comision, monto_neto,
                monto_bruto - costo, ganancia
            ))
            
            return {
                "success": True,
                "message": "Venta registrada",
                "cantidad": datos.cantidad,
                "precio_venta": datos.precio_venta,
                "monto_bruto": round(monto_bruto, 2),
                "comision": round(comision, 2),
                "monto_neto": round(monto_neto, 2),
                "ganancia": round(ganancia, 2)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/cerrar-dia")
async def cerrar_dia():
    """Cierra el día actual"""
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM dias WHERE estado = 'abierto' ORDER BY id DESC LIMIT 1")
            dia = cursor.fetchone()
            
            if not dia:
                raise HTTPException(status_code=404, detail="No hay día activo")
            
            # Calcular totales
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(efectivo_recibido), 0) as total_efectivo,
                    COALESCE(SUM(comision), 0) as total_comision,
                    COALESCE(SUM(ganancia_neta), 0) as total_ganancia
                FROM ventas WHERE dia_id = ?
            """, (dia['id'],))
            totales = cursor.fetchone()
            
            capital_final = totales['total_efectivo']
            
            # Actualizar día
            cursor.execute("""
                UPDATE dias SET
                    capital_final = ?,
                    efectivo_recibido = ?,
                    comisiones_pagadas = ?,
                    ganancia_neta = ?,
                    estado = 'cerrado',
                    fecha_cierre = datetime('now')
                WHERE id = ?
            """, (
                capital_final,
                totales['total_efectivo'],
                totales['total_comision'],
                totales['total_ganancia'],
                dia['id']
            ))
            
            # Actualizar ciclo
            cursor.execute("""
                UPDATE ciclos SET
                    dias_operados = dias_operados + 1,
                    ganancia_total = ganancia_total + ?
                WHERE id = ?
            """, (totales['total_ganancia'], dia['ciclo_id']))
            
            return {
                "success": True,
                "message": "Día cerrado",
                "capital_inicial": dia['capital_inicial'],
                "capital_final": capital_final,
                "ganancia": totales['total_ganancia']
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/historial-ventas")
async def get_historial_ventas(dia_id: Optional[int] = None, limite: int = 50):
    """Obtiene el historial de ventas"""
    try:
        with db.get_cursor(commit=False) as cursor:
            if dia_id:
                cursor.execute("""
                    SELECT v.*, c.nombre as cripto_nombre, c.simbolo as cripto_simbolo
                    FROM ventas v
                    JOIN criptomonedas c ON v.cripto_id = c.id
                    WHERE v.dia_id = ?
                    ORDER BY v.fecha DESC
                """, (dia_id,))
            else:
                cursor.execute("""
                    SELECT v.*, c.nombre as cripto_nombre, c.simbolo as cripto_simbolo
                    FROM ventas v
                    JOIN criptomonedas c ON v.cripto_id = c.id
                    ORDER BY v.fecha DESC
                    LIMIT ?
                """, (limite,))
            
            ventas = cursor.fetchall()
            
            return [Venta(
                id=v['id'],
                cantidad=v['cantidad'],
                precio_venta=v['precio_unitario'],
                monto_bruto=v['monto_venta'],
                comision=v['comision'],
                monto_neto=v['efectivo_recibido'],
                ganancia=v['ganancia_neta'],
                fecha=v['fecha']
            ) for v in ventas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
