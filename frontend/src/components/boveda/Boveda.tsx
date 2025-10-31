import { useEffect, useState } from 'react';
import { getBovedaResumen, getBovedaInventario, agregarCapital, retirarCapital } from '../../services/api';
import type { BovedaData, Criptomoneda } from '../../types';

// Lista de criptos del sistema
const CRIPTOS_SISTEMA = [
  { id: 1, nombre: 'Tether', simbolo: 'USDT' },
  { id: 2, nombre: 'USD Coin', simbolo: 'USDC' },
  { id: 3, nombre: 'Binance USD', simbolo: 'BUSD' },
  { id: 4, nombre: 'Bitcoin', simbolo: 'BTC' },
  { id: 5, nombre: 'Ethereum', simbolo: 'ETH' },
  { id: 6, nombre: 'Binance Coin', simbolo: 'BNB' },
  { id: 7, nombre: 'Dai', simbolo: 'DAI' }
];

export default function Boveda() {
  const [data, setData] = useState<BovedaData | null>(null);
  const [inventario, setInventario] = useState<Criptomoneda[]>([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState<'resumen' | 'agregar' | 'retirar'>('resumen');
  const [mensaje, setMensaje] = useState<{tipo: 'success' | 'error' | 'warning', texto: string} | null>(null);
  
  // Formularios
  const [simbolo, setSimbolo] = useState('USDT');
  const [cantidad, setCantidad] = useState('');
  const [precioUsd, setPrecioUsd] = useState('1.0');
  const [razon, setRazon] = useState('');

  const fetchData = async () => {
    try {
      const [resumenRes, inventarioRes] = await Promise.all([
        getBovedaResumen(),
        getBovedaInventario()
      ]);
      setData(resumenRes.data);
      setInventario(inventarioRes.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const mostrarMensaje = (tipo: 'success' | 'error' | 'warning', texto: string) => {
    setMensaje({ tipo, texto });
    setTimeout(() => setMensaje(null), 5000);
  };

  const handleAgregar = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const cant = parseFloat(cantidad);
    const precio = parseFloat(precioUsd);
    
    if (isNaN(cant) || cant <= 0) {
      mostrarMensaje('error', 'Cantidad inválida');
      return;
    }
    
    if (isNaN(precio) || precio <= 0) {
      mostrarMensaje('error', 'Precio inválido');
      return;
    }

    try {
      const response = await agregarCapital({ 
        simbolo: simbolo.toUpperCase(), 
        cantidad: cant, 
        precio_usd: precio 
      });
      
      mostrarMensaje('success', response.data.message || 'Capital agregado exitosamente');
      setSimbolo('USDT');
      setCantidad('');
      setPrecioUsd('1.0');
      setVista('resumen');
      fetchData();
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Error al agregar capital';
      mostrarMensaje('error', detail);
    }
  };

  const handleRetirar = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const cant = parseFloat(cantidad);
    
    if (isNaN(cant) || cant <= 0) {
      mostrarMensaje('error', 'Cantidad inválida');
      return;
    }

    try {
      const response = await retirarCapital({ 
        simbolo: simbolo.toUpperCase(), 
        cantidad: cant,
        razon: razon || undefined
      });
      
      mostrarMensaje('success', response.data.message || 'Capital retirado exitosamente');
      setSimbolo('USDT');
      setCantidad('');
      setRazon('');
      setVista('resumen');
      fetchData();
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Error al retirar capital';
      mostrarMensaje('error', detail);
    }
  };

  if (loading) return <div className="p-8">Cargando...</div>;
  if (!data) return <div className="p-8">Error al cargar datos</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Bóveda de Capital</h1>

      {/* Mensajes */}
      {mensaje && (
        <div className={`mb-6 p-4 rounded-lg ${
          mensaje.tipo === 'success' ? 'bg-green-50 border-l-4 border-green-400' :
          mensaje.tipo === 'error' ? 'bg-red-50 border-l-4 border-red-400' :
          'bg-yellow-50 border-l-4 border-yellow-400'
        }`}>
          <p className={
            mensaje.tipo === 'success' ? 'text-green-700' :
            mensaje.tipo === 'error' ? 'text-red-700' :
            'text-yellow-700'
          }>{mensaje.texto}</p>
        </div>
      )}

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Capital Total USD</h3>
          <p className="text-3xl font-bold text-green-600">${data.capital_total_usd.toLocaleString()}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Número de Criptos</h3>
          <p className="text-2xl font-bold">{data.numero_criptos}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setVista('resumen')}
          className={`px-4 py-2 rounded ${vista === 'resumen' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Inventario
        </button>
        <button
          onClick={() => setVista('agregar')}
          className={`px-4 py-2 rounded ${vista === 'agregar' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Agregar
        </button>
        <button
          onClick={() => setVista('retirar')}
          className={`px-4 py-2 rounded ${vista === 'retirar' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Retirar
        </button>
      </div>

      {/* Vista Inventario */}
      {vista === 'resumen' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Inventario de Criptomonedas</h2>
          
          {inventario.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No hay criptomonedas en la bóveda</p>
              <button
                onClick={() => setVista('agregar')}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Agregar Capital
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">Cripto</th>
                    <th className="px-4 py-2 text-left">Cantidad</th>
                    <th className="px-4 py-2 text-left">Valor USD</th>
                    <th className="px-4 py-2 text-left">% Cartera</th>
                  </tr>
                </thead>
                <tbody>
                  {inventario.map(c => (
                    <tr key={c.simbolo} className="border-t">
                      <td className="px-4 py-2">
                        <div className="font-bold">{c.simbolo}</div>
                        <div className="text-sm text-gray-500">{c.nombre}</div>
                      </td>
                      <td className="px-4 py-2">{c.cantidad.toFixed(4)}</td>
                      <td className="px-4 py-2">${c.valor_usd.toLocaleString()}</td>
                      <td className="px-4 py-2">
                        <span className="font-medium">{c.porcentaje_cartera}%</span>
                        <div className="text-xs text-gray-500">de tu capital total</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Vista Agregar */}
      {vista === 'agregar' && (
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <h2 className="text-xl font-bold mb-4">Agregar Capital</h2>
          
          <form onSubmit={handleAgregar} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Criptomoneda</label>
              <select
                value={simbolo}
                onChange={(e) => setSimbolo(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                required
              >
                {CRIPTOS_SISTEMA.map(c => (
                  <option key={c.id} value={c.simbolo}>
                    {c.simbolo} - {c.nombre}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">Selecciona la cripto que compraste</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Cantidad de Cripto</label>
              <input
                type="number"
                step="0.00000001"
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder="1000"
                required
              />
              <p className="text-xs text-gray-500 mt-1">Cuánto cripto compraste</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Precio Promedio (USD por cripto)</label>
              <input
                type="number"
                step="0.00000001"
                value={precioUsd}
                onChange={(e) => setPrecioUsd(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder="1.0"
                required
              />
              <p className="text-xs text-gray-500 mt-1">A qué precio lo compraste (Ej: 1.050)</p>
            </div>

            <button
              type="submit"
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
            >
              Agregar Capital
            </button>
          </form>
        </div>
      )}

      {/* Vista Retirar */}
      {vista === 'retirar' && (
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <h2 className="text-xl font-bold mb-4">Retirar Capital</h2>
          
          {inventario.length === 0 ? (
            <p className="text-gray-500">No hay criptomonedas para retirar</p>
          ) : (
            <form onSubmit={handleRetirar} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Criptomoneda</label>
                <select
                  value={simbolo}
                  onChange={(e) => setSimbolo(e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                  required
                >
                  {inventario.map(c => (
                    <option key={c.simbolo} value={c.simbolo}>
                      {c.simbolo} - Disponible: {c.cantidad.toFixed(4)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Cantidad</label>
                <input
                  type="number"
                  step="0.00000001"
                  value={cantidad}
                  onChange={(e) => setCantidad(e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                  placeholder="1000"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Razón (opcional)</label>
                <input
                  type="text"
                  value={razon}
                  onChange={(e) => setRazon(e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                  placeholder="Motivo del retiro"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700"
              >
                Retirar Capital
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
