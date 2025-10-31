// Dashboard
export interface DashboardData {
  capital_total: number;
  ganancia_total: number;
  ciclos_completados: number;
  ventas_hoy: number;
  rendimiento_porcentual: number;
  ultima_actualizacion: string;
}

// Bóveda
export interface BovedaData {
  capital_total_usd: number;
  numero_criptos: number;
  ultima_actualizacion: string;
}

export interface Criptomoneda {
  simbolo: string;
  nombre: string;
  cantidad: number;
  valor_usd: number;
  porcentaje_cartera: number;
}

// Operaciones
export interface DiaOperativo {
  id: number;
  fecha: string;
  estado: string;
  precio_publicado: number;
  criptomoneda: string;
  ventas_realizadas: number;
  capital_inicial: number;
  ganancia_neta: number;
  fecha_creacion: string;
}

export interface Venta {
  id: number;
  dia_id: number;
  precio_venta: number;
  cantidad: number;
  comision: number;
  ganancia: number;
  fecha: string;
}

// Ciclos
export interface Ciclo {
  id: number;
  numero: number;
  fecha_inicio: string;
  fecha_fin?: string;
  capital_inicial: number;
  capital_final?: number;
  ganancia_total?: number;
  rendimiento_porcentual?: number;
  dias_operados: number;
  ventas_totales: number;
  estado: string;
}
