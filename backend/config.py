"""
Configuración centralizada del sistema
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Información del proyecto
    PROJECT_NAME: str = "Sistema de Arbitraje P2P"
    VERSION: str = "1.0.0"
    
    # Base de datos
    DATABASE_PATH: str = "data/arbitraje.db"
    
    # Seguridad
    SECRET_KEY: str = "tu-secret-key-super-segura"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Usuario admin por defecto
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@arbitraje.local"
    
    # Configuración operativa
    COMISION_DEFECTO: float = 0.35
    GANANCIA_OBJETIVO_DEFECTO: float = 2.0
    MIN_VENTAS_DIA: int = 5
    MAX_VENTAS_DIA: int = 8
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancia global
settings = Settings()

# Función para crear directorios
def init_directories():
    """Crear directorios necesarios si no existen"""
    dirs = ["data", "logs", "backups", "reportes", "graficos"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
