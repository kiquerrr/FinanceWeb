#!/bin/bash
echo "🚀 Iniciando Sistema de Arbitraje P2P API..."
echo ""

cd /root/arbitraje_p2p_web/backend

# Activar entorno virtual
source venv_backend/bin/activate

# Iniciar servidor
python main.py
