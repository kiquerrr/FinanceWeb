"""
Rutas de Configuración
Gestión de configuración del sistema
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

router = APIRouter()

# Modelos
class ConfigGeneral(BaseModel):
    comision_defecto: float = Field(..., ge=0, le=100)
    ganancia_objetivo: float = Field(..., gt=0)
    min_ventas_dia: int = Field(..., ge=0)
    max_ventas_dia: int = Field(..., ge=0)

class ConfigSistema(BaseModel):
    nombre_sistema: str
    version: str
    database: str
    python_version: str
    api_framework: str

class ActualizarConfigRequest(BaseModel):
    comision_defecto: Optional[float] = Field(None, ge=0, le=100)
    ganancia_objetivo: Optional[float] = Field(None, gt=0)
    min_ventas_dia: Optional[int] = Field(None, ge=0)
    max_ventas_dia: Optional[int] = Field(None, ge=0)

# Endpoints
@router.get("/general", response_model=ConfigGeneral)
async def get_config_general():
    """Obtener configuración general"""
    try:
        return ConfigGeneral(
            comision_defecto=settings.COMISION_DEFECTO,
            ganancia_objetivo=settings.GANANCIA_OBJETIVO_DEFECTO,
            min_ventas_dia=settings.MIN_VENTAS_DIA,
            max_ventas_dia=settings.MAX_VENTAS_DIA
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/general")
async def actualizar_config_general(datos: ActualizarConfigRequest):
    """Actualizar configuración en memoria (temporal hasta reinicio)"""
    try:
        campos_actualizados = {}
        
        if datos.comision_defecto is not None:
            settings.COMISION_DEFECTO = datos.comision_defecto
            campos_actualizados['comision_defecto'] = datos.comision_defecto
        
        if datos.ganancia_objetivo is not None:
            settings.GANANCIA_OBJETIVO_DEFECTO = datos.ganancia_objetivo
            campos_actualizados['ganancia_objetivo'] = datos.ganancia_objetivo
        
        if datos.min_ventas_dia is not None:
            settings.MIN_VENTAS_DIA = datos.min_ventas_dia
            campos_actualizados['min_ventas_dia'] = datos.min_ventas_dia
        
        if datos.max_ventas_dia is not None:
            settings.MAX_VENTAS_DIA = datos.max_ventas_dia
            campos_actualizados['max_ventas_dia'] = datos.max_ventas_dia
        
        return {
            "success": True,
            "message": "Configuración actualizada correctamente",
            "campos_actualizados": campos_actualizados,
            "nota": "Los cambios están activos pero son temporales (hasta reiniciar servidor). Para hacerlos permanentes, edita backend/config.py",
            "timestamp": datetime.now()
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/sistema")
async def get_config_sistema():
    """Obtener información del sistema"""
    import sys
    import fastapi
    
    return ConfigSistema(
        nombre_sistema=settings.PROJECT_NAME,
        version=settings.VERSION,
        database="SQLite",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        api_framework=f"FastAPI {fastapi.__version__}"
    )

@router.post("/reset-configuracion")
async def reset_configuracion():
    """Restaurar configuración a valores por defecto"""
    try:
        settings.COMISION_DEFECTO = 0.35
        settings.GANANCIA_OBJETIVO_DEFECTO = 2.0
        settings.MIN_VENTAS_DIA = 5
        settings.MAX_VENTAS_DIA = 8
        
        return {
            "success": True,
            "message": "Configuración restaurada a valores por defecto",
            "timestamp": datetime.now()
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/test")
async def test_configuracion():
    """Endpoint de prueba"""
    return {
        "message": "Módulo de configuración funcionando",
        "storage": "En memoria (temporal)",
        "timestamp": datetime.now().isoformat()
    }
