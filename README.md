# 🚀 Sistema de Arbitraje P2P - Web API

Sistema profesional de arbitraje P2P con API REST completa, gestión de capital y operaciones en tiempo real.

![Status](https://img.shields.io/badge/status-operational-success)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Endpoints](https://img.shields.io/badge/endpoints-18%20activos-success)

---

## ✨ Características

- ✅ **18 Endpoints con Datos Reales**
- ✅ **Sistema Operativo Completo**
- ✅ **Gestión de Capital Dinámica**
- ✅ **Dashboard en Tiempo Real**
- ✅ **Documentación Swagger Automática**
- ✅ **Arquitectura Profesional y Escalable**

---

## 📊 Estado Actual
```
💰 Capital en Bóveda:    $13,600
📈 Ventas Registradas:   3
💵 Ganancia Generada:    $0.24
🔄 Ciclos Activos:       1
⚙️  Endpoints Activos:    18/31 (58%)
```

---

## 🏗️ Arquitectura
```
Sistema de Arbitraje P2P
│
├── 🌐 API REST (FastAPI)
│   ├── 31 endpoints totales
│   ├── 18 con datos reales
│   └── Documentación Swagger
│
├── 💾 Base de Datos (SQLite)
│   ├── 8 tablas principales
│   └── Datos inicializados
│
└── 📚 Documentación
    ├── README.md
    ├── INSTALACION_COMPLETADA.md
    ├── INTEGRACION_COMPLETADA.md
    ├── SESION_COMPLETA_FASE_2_Y_3.md
    └── SESION_FINAL_18_ENDPOINTS.md
```

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.11+
- pip
- tmux (opcional, para servidor permanente)

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/kiquerrr/FinanceWeb.git
cd FinanceWeb

# Crear entorno virtual
cd backend
python -m venv venv_backend
source venv_backend/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python main.py
```

### Acceder

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/health

---

## 📡 Endpoints Disponibles

### 🏦 Bóveda (5 endpoints)
- `GET /api/boveda/inventario` - Lista de criptomonedas
- `GET /api/boveda/resumen` - Capital total
- `GET /api/boveda/cripto/{simbolo}` - Info individual
- `POST /api/boveda/agregar-capital` - Agregar fondos
- `POST /api/boveda/retirar-capital` - Retirar fondos

### 🔄 Ciclos (4 endpoints)
- `GET /api/ciclos/activo` - Ciclo actual
- `GET /api/ciclos/historial` - Ciclos finalizados
- `GET /api/ciclos/{id}` - Ciclo específico
- `GET /api/ciclos/{id}/estadisticas` - Estadísticas

### 📊 Dashboard (2 endpoints)
- `GET /api/dashboard/resumen` - Resumen general
- `GET /api/dashboard/metricas` - 4 tarjetas de métricas

### 💼 Operaciones (4 endpoints)
- `POST /api/operaciones/iniciar-dia` - Crear día operativo
- `POST /api/operaciones/registrar-venta` - Registrar venta
- `GET /api/operaciones/dia-actual` - Ver día activo
- `GET /api/operaciones/historial-ventas` - Historial

### ⚙️ Configuración (3 endpoints)
- `GET /api/config/general` - Ver configuración
- `PUT /api/config/general` - Actualizar
- `POST /api/config/reset-configuracion` - Restaurar

---

## 💡 Ejemplos de Uso

### Ver Dashboard
```bash
curl http://localhost:8000/api/dashboard/resumen | python -m json.tool
```

### Registrar Venta
```bash
curl -X POST http://localhost:8000/api/operaciones/registrar-venta \
  -H "Content-Type: application/json" \
  -d '{
    "precio_venta": 1.01,
    "cantidad": 100,
    "comision": 0.35
  }'
```

### Agregar Capital
```bash
curl -X POST http://localhost:8000/api/boveda/agregar-capital \
  -H "Content-Type: application/json" \
  -d '{
    "simbolo": "USDT",
    "cantidad": 1000,
    "precio_usd": 1.0
  }'
```

---

## 🛠️ Tecnologías

- **Backend:** FastAPI 0.104.1
- **Base de Datos:** SQLite
- **Validación:** Pydantic
- **Documentación:** Swagger/OpenAPI
- **Python:** 3.11.2

---

## 📈 Roadmap

- [x] API REST completa
- [x] 18 endpoints con datos reales
- [x] Sistema operativo funcional
- [ ] Frontend React (Fase 4)
- [ ] Autenticación JWT completa
- [ ] Deploy a producción
- [ ] Gráficos en tiempo real

---

## 📝 Documentación

Ver documentación detallada en:
- [Instalación Completa](INSTALACION_COMPLETADA.md)
- [Integración con BD](INTEGRACION_COMPLETADA.md)
- [Sesión Completa Fases 2-3](SESION_COMPLETA_FASE_2_Y_3.md)
- [Resumen Final 18 Endpoints](SESION_FINAL_18_ENDPOINTS.md)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios.

---

## 📄 Licencia

Este proyecto está bajo licencia MIT.

---

## 👤 Autor

**kiquerrr**
- GitHub: [@kiquerrr](https://github.com/kiquerrr)

---

## 🎯 Estado del Proyecto
```
FASE 1: Instalación              ████████████ 100%
FASE 2: Integración BD            ████████████ 100%
FASE 3: Completar Funcionalidad   ████████████ 100%
FASE 4: Frontend React            ░░░░░░░░░░░░   0%
FASE 5: Producción                ░░░░░░░░░░░░   0%
```

**Sistema:** 🟢 OPERACIONAL  
**Última actualización:** 29 de Octubre 2025  
**Tiempo de desarrollo:** 8 horas
