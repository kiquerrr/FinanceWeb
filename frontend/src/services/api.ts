import axios from 'axios';

const API_BASE_URL = 'http://10.68.222.26:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ===== DASHBOARD =====
export const getDashboardResumen = () => api.get('/dashboard/resumen');
export const getDashboardMetricas = () => api.get('/dashboard/metricas');

// ===== BÓVEDA =====
export const getBovedaResumen = () => api.get('/boveda/resumen');
export const getBovedaInventario = () => api.get('/boveda/inventario');
export const agregarCapital = (data: { 
  simbolo: string; 
  monto_usd: number; 
  precio_unitario: number;
}) => api.post('/boveda/agregar-capital', data);
export const retirarCapital = (data: { simbolo: string; cantidad: number; razon?: string }) => 
  api.post('/boveda/retirar-capital', data);

// ===== OPERACIONES =====
export const iniciarDia = (data: { 
  cripto_id: number; 
  capital_usd: number; 
  tasa_compra: number;
  ganancia_objetivo_pct?: number;
  comision_pct?: number;
}) => api.post('/operaciones/iniciar-dia', data);

export const registrarVenta = (data: { cantidad: number; precio_venta: number }) =>
  api.post('/operaciones/registrar-venta', data);

export const getDiaActual = () => api.get('/operaciones/dia-actual');
export const cerrarDia = () => api.post('/operaciones/cerrar-dia');
export const getHistorialVentas = (dia_id?: number, limite?: number) => 
  api.get('/operaciones/historial-ventas', { params: { dia_id, limite } });

// ===== CICLOS =====
export const getCicloActivo = () => api.get('/ciclos/activo');
export const crearCiclo = (data: { capital_inicial: number }) =>
  api.post('/ciclos/iniciar', data);
