"""
API Routes Module
Exporta todos los routers
"""
from . import auth
from . import dashboard
from . import operaciones
from . import boveda
from . import ciclos
from . import configuracion

__all__ = [
    'auth',
    'dashboard', 
    'operaciones',
    'boveda',
    'ciclos',
    'configuracion'
]
