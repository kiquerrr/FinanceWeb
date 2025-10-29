"""
Rutas de Bóveda - Gestión de capital y criptomonedas
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db_manager import db

router = APIRouter()

class Criptomoneda(BaseModel):
    simbolo: str
    nombre: str
    cantidad: float
    valor_usd: float
    porcentaje_cartera: float

class ResumenBoveda(BaseModel):
    capital_total_usd: float
    numero_criptos: int
    ultima_actualizacion: datetime

class AgregarCapitalRequest(BaseModel):
    simbolo: str
    cantidad: float = Field(..., gt=0)
    precio_usd: float = Field(..., gt=0)

class RetirarCapitalRequest(BaseModel):
    simbolo: str
    cantidad: float = Field(..., gt=0)
    razon: Optional[str] = None

@router.get("/inventario", response_model=List[Criptomoneda])
async def get_inventario():
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT c.simbolo, c.nombre, b.cantidad, b.precio_promedio,
                       (b.cantidad * b.precio_promedio) as valor_total
                FROM boveda_ciclo b
                JOIN criptomonedas c ON b.cripto_id = c.id
                JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo'
                ORDER BY valor_total DESC
            """)
            rows = cursor.fetchall()
            if not rows:
                return []
            capital_total = sum(row['valor_total'] for row in rows)
            return [Criptomoneda(
                simbolo=row['simbolo'], nombre=row['nombre'],
                cantidad=row['cantidad'], valor_usd=row['valor_total'],
                porcentaje_cartera=round((row['valor_total'] / capital_total * 100), 2)
            ) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/resumen", response_model=ResumenBoveda)
async def get_resumen_boveda():
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as num_criptos,
                       SUM(b.cantidad * b.precio_promedio) as capital_total
                FROM boveda_ciclo b
                JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo'
            """)
            row = cursor.fetchone()
            return ResumenBoveda(
                capital_total_usd=row['capital_total'] or 0.0,
                numero_criptos=row['num_criptos'] or 0,
                ultima_actualizacion=datetime.now()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/cripto/{simbolo}", response_model=Criptomoneda)
async def get_info_cripto(simbolo: str):
    try:
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT c.simbolo, c.nombre, b.cantidad, b.precio_promedio,
                       (b.cantidad * b.precio_promedio) as valor_total
                FROM boveda_ciclo b
                JOIN criptomonedas c ON b.cripto_id = c.id
                JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo' AND c.simbolo = ?
            """, (simbolo.upper(),))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Criptomoneda no encontrada")
            cursor.execute("""
                SELECT SUM(b.cantidad * b.precio_promedio) as total
                FROM boveda_ciclo b JOIN ciclos cy ON b.ciclo_id = cy.id
                WHERE cy.estado = 'activo'
            """)
            capital_total = cursor.fetchone()['total']
            return Criptomoneda(
                simbolo=row['simbolo'], nombre=row['nombre'],
                cantidad=row['cantidad'], valor_usd=row['valor_total'],
                porcentaje_cartera=round((row['valor_total'] / capital_total * 100), 2)
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/agregar-capital")
async def agregar_capital(datos: AgregarCapitalRequest):
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM ciclos WHERE estado = 'activo' LIMIT 1")
            ciclo = cursor.fetchone()
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            cursor.execute("SELECT id FROM criptomonedas WHERE simbolo = ?", (datos.simbolo.upper(),))
            cripto = cursor.fetchone()
            if not cripto:
                raise HTTPException(status_code=404, detail="Criptomoneda no encontrada")
            
            cursor.execute("""
                SELECT id, cantidad, precio_promedio FROM boveda_ciclo
                WHERE ciclo_id = ? AND cripto_id = ?
            """, (ciclo['id'], cripto['id']))
            boveda = cursor.fetchone()
            
            if boveda:
                cantidad_nueva = boveda['cantidad'] + datos.cantidad
                precio_promedio_nuevo = (
                    (boveda['cantidad'] * boveda['precio_promedio']) + 
                    (datos.cantidad * datos.precio_usd)
                ) / cantidad_nueva
                cursor.execute("""
                    UPDATE boveda_ciclo SET cantidad = ?, precio_promedio = ?
                    WHERE id = ?
                """, (cantidad_nueva, precio_promedio_nuevo, boveda['id']))
                mensaje = f"Actualizado: ahora tienes {cantidad_nueva} {datos.simbolo}"
            else:
                cursor.execute("""
                    INSERT INTO boveda_ciclo (ciclo_id, cripto_id, cantidad, precio_promedio)
                    VALUES (?, ?, ?, ?)
                """, (ciclo['id'], cripto['id'], datos.cantidad, datos.precio_usd))
                mensaje = f"Agregado: {datos.cantidad} {datos.simbolo}"
            
            return {
                "success": True,
                "message": mensaje,
                "simbolo": datos.simbolo,
                "cantidad_agregada": datos.cantidad,
                "valor_total_agregado": round(datos.cantidad * datos.precio_usd, 2)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/retirar-capital")
async def retirar_capital(datos: RetirarCapitalRequest):
    try:
        with db.get_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM ciclos WHERE estado = 'activo' LIMIT 1")
            ciclo = cursor.fetchone()
            if not ciclo:
                raise HTTPException(status_code=400, detail="No hay ciclo activo")
            
            cursor.execute("""
                SELECT b.id, b.cantidad, b.precio_promedio
                FROM boveda_ciclo b
                JOIN criptomonedas c ON b.cripto_id = c.id
                WHERE b.ciclo_id = ? AND c.simbolo = ?
            """, (ciclo['id'], datos.simbolo.upper()))
            boveda = cursor.fetchone()
            
            if not boveda:
                raise HTTPException(status_code=404, detail="Cripto no encontrada en bóveda")
            if boveda['cantidad'] < datos.cantidad:
                raise HTTPException(status_code=400, detail=f"Insuficiente. Disponible: {boveda['cantidad']}")
            
            cantidad_nueva = boveda['cantidad'] - datos.cantidad
            
            if cantidad_nueva <= 0:
                cursor.execute("DELETE FROM boveda_ciclo WHERE id = ?", (boveda['id'],))
                mensaje = f"Retirado todo el {datos.simbolo}"
            else:
                cursor.execute("UPDATE boveda_ciclo SET cantidad = ? WHERE id = ?",
                             (cantidad_nueva, boveda['id']))
                mensaje = f"Retirado: {datos.cantidad}. Quedan: {cantidad_nueva}"
            
            return {
                "success": True,
                "message": mensaje,
                "simbolo": datos.simbolo,
                "cantidad_retirada": datos.cantidad,
                "valor_retirado": round(datos.cantidad * boveda['precio_promedio'], 2),
                "cantidad_restante": max(0, cantidad_nueva)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/test")
async def test_boveda():
    return {"message": "Bóveda OK", "timestamp": datetime.now().isoformat()}
