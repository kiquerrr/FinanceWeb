# 🚀 Sistema de Arbitraje P2P - Fase Web v1.0

Sistema web completo para gestión de operaciones de arbitraje P2P en criptomonedas.

**Backend:** FastAPI + Python  
**Base de datos:** SQLite  
**Autenticación:** JWT (próximamente)

---

## ✅ INSTALACIÓN COMPLETADA

El sistema está instalado y funcionando.

---

## 🎯 INICIO RÁPIDO

### **Opción A: Usar tmux (Servidor en background)**
```bash
# Ver si el servidor ya está corriendo
tmux ls

# Conectar a la sesión existente
tmux attach -t api_server

# Dentro de tmux:
# - Ctrl+B, D  → Desconectar (servidor sigue corriendo)
# - Ctrl+C     → Detener servidor
```

### **Opción B: Iniciar manualmente**
```bash
cd /root/arbitraje_p2p_web/backend
./start.sh
```

---

## 🌐 ACCEDER AL SISTEMA

- **API:** http://10.68.222.26:8000
- **Documentación:** http://10.68.222.26:8000/api/docs
- **Health Check:** http://10.68.222.26:8000/health

---

## 📂 ESTRUCTURA DEL PROYECTO
```
/root/arbitraje_p2p_web/
├── backend/
│   ├── core/              # Módulos fundamentales
│   ├── modules/           # Módulos principales
│   ├── features/          # Funcionalidades avanzadas
│   ├── api/               # Rutas del API
│   ├── main.py            # Servidor FastAPI
│   ├── config.py          # Configuración
│   ├── start.sh           # Script de inicio
│   └── venv_backend/      # Entorno virtual
├── data_test/             # Datos de prueba
├── docs/                  # Documentación
└── frontend/              # React (futuro)
```

---

## 🔧 COMANDOS ÚTILES
```bash
# Ver estado del servidor
tmux ls
curl http://localhost:8000/health

# Conectar al servidor
tmux attach -t api_server

# Detener el servidor
tmux attach -t api_server
# (dentro de tmux) Ctrl+C

# Reiniciar el servidor
cd /root/arbitraje_p2p_web/backend
./start.sh

# Ver logs en tiempo real
# (dentro de tmux donde corre el servidor)
```

---

## 📝 CONFIGURACIÓN

Archivo: `/root/arbitraje_p2p_web/backend/.env` (crear desde .env.example)
```bash
cd /root/arbitraje_p2p_web/backend
cp .env.example .env
nano .env
```

Variables importantes:
- `SECRET_KEY` - Cambiar en producción
- `ADMIN_PASSWORD` - Cambiar el password por defecto
- `DATABASE_PATH` - Ruta de la base de datos

---

## 🧪 PROBAR EL SISTEMA
```bash
# Health check
curl http://localhost:8000/health

# Info del API
curl http://localhost:8000

# Documentación interactiva
# Abrir en navegador: http://10.68.222.26:8000/api/docs
```

---

## 📚 PRÓXIMOS PASOS

1. **Conectar endpoints con tu código real**
   - Los endpoints actuales devuelven datos de ejemplo
   - Necesitas conectarlos con tus módulos en `core/`, `modules/`, `features/`

2. **Crear rutas del API**
   - Autenticación (login, JWT)
   - Dashboard (métricas, resúmenes)
   - Operaciones (día operativo)
   - Bóveda (gestión de capital)
   - Ciclos (gestión de ciclos)

3. **Frontend React**
   - Interfaz de usuario moderna
   - Gráficos en tiempo real

---

## 🔒 SEGURIDAD

**ANTES DE PRODUCCIÓN:**
- [ ] Cambiar SECRET_KEY en .env
- [ ] Cambiar ADMIN_PASSWORD
- [ ] Configurar CORS correctamente
- [ ] Usar HTTPS
- [ ] Configurar firewall

---

## 🆘 SOPORTE

### Servidor no inicia
```bash
# Ver si el puerto está ocupado
ss -tuln | grep 8000

# Matar procesos en el puerto 8000
fuser -k 8000/tcp

# Reiniciar
cd /root/arbitraje_p2p_web/backend
./start.sh
```

### Ver logs
```bash
# Conectar a tmux donde corre el servidor
tmux attach -t api_server
```

### Reinstalar dependencias
```bash
cd /root/arbitraje_p2p_web/backend
source venv_backend/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

## 📞 CONTACTO

- Proyecto original: `/root/arbitraje_p2p_control/`
- GitHub: https://github.com/kiquerrr/Finance

---

**Versión:** 1.0.0  
**Última actualización:** Octubre 2025  
**Estado:** Funcional - Listo para desarrollo
