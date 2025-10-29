"""
Sistema de Arbitraje P2P - Backend API
Servidor principal FastAPI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar configuración
from config import settings, init_directories

# Importar routers
from api.routes import auth, dashboard, operaciones, boveda, ciclos, configuracion

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST para gestión de arbitraje P2P en criptomonedas",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar el servidor"""
    print("🚀 Iniciando Sistema de Arbitraje P2P API...")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Crear directorios necesarios
    init_directories()
    print("✅ Directorios inicializados")
    
    print("📡 Registrando rutas del API...")
    print("✅ Servidor listo")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar el servidor"""
    print("👋 Cerrando servidor...")

# Endpoints principales
@app.get("/")
async def root():
    """Endpoint raíz - Información del API"""
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "docs": "/api/docs",
        "endpoints": {
            "auth": "/api/auth",
            "dashboard": "/api/dashboard",
            "operaciones": "/api/operaciones",
            "boveda": "/api/boveda",
            "ciclos": "/api/ciclos",
            "configuracion": "/api/config"
        }
    }

@app.get("/health")
async def health_check():
    """Health check para monitoreo"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Registrar routers
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(operaciones.router, prefix="/api/operaciones", tags=["Operaciones"])
app.include_router(boveda.router, prefix="/api/boveda", tags=["Bóveda"])
app.include_router(ciclos.router, prefix="/api/ciclos", tags=["Ciclos"])
app.include_router(configuracion.router, prefix="/api/config", tags=["Configuración"])

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Configuración del servidor
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
