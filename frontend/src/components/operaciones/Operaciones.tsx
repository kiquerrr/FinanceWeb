import { useEffect, useState } from 'react';
import { 
  getDiaActual, 
  iniciarDia, 
  cerrarDia, 
  registrarVenta, 
  getHistorialVentas,
  getCicloActivo,
  getBovedaInventario
} from '../../services/api';
import type { DiaOperativo, Venta, Criptomoneda } from '../../types';

export default function Operaciones() {
  const [dia, setDia] = useState<DiaOperativo | null>(null);
  const [ventas, setVentas] = useState<Venta[]>([]);
  const [criptos, setCriptos] = useState<Criptomoneda[]>([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState<'dia' | 'ventas'>('dia');
  const [hayCiclo, setHayCiclo] = useState(false);
  const [mensaje, setMensaje] = useState<{tipo: 'success' | 'error' | 'warning', texto: string} | null>(null);
  
  // Formulario iniciar día
  const [criptoId, setCriptoId] = useState<number>(1);
  const [capitalUsd, setCapitalUsd] = useState('');
  const [tasaCompra, setTasaCompra] = useState('');
  
  // Formulario venta
  const [precioVenta, setPrecioVenta] = useState('');
  const [cantidad, setCantidad] = useState('');

  const fetchDia = async () => {
    try {
      const response = await getDiaActual();
      setDia(response.data);
      fetchVentas(response.data.id);
    } catch (error: any) {
      if (error.response?.status === 404) {
        setDia(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchVentas = async (diaId: number) => {
    try {
      const response = await getHistorialVentas(diaId);
      setVentas(response.data);
    } catch (error) {
      console.error('Error cargando ventas:', error);
    }
  };

  const fetchCriptos = async () => {
    try {
      const response = await getBovedaInventario();
      setCriptos(response.data);
      if (response.data.length > 0) {
        setCriptoId(response.data[0].simbolo === 'USDT' ? 1 : response.data[0].simbolo);
      }
    } catch (error) {
      console.error('Error cargando criptos:', error);
    }
  };

  const verificarCiclo = async () => {
    try {
      await getCicloActivo();
      setHayCiclo(true);
    } catch {
      setHayCiclo(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      await verificarCiclo();
      await fetchCriptos();
      await fetchDia();
    };
    init();
  }, []);

  const mostrarMensaje = (tipo: 'success' | 'error' | 'warning', texto: string) => {
    setMensaje({ tipo, texto });
    setTimeout(() => setMensaje(null), 5000);
  };

  const handleIniciarDia = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!hayCiclo) {
      mostrarMensaje('error', '⚠️ No hay ciclo activo. Crea un ciclo primero.');
      return;
    }
    
    const capital = parseFloat(capitalUsd);
    const tasa = parseFloat(tasaCompra);
    
    if (isNaN(capital) || capital <= 0) {
      mostrarMensaje('error', 'Capital inválido');
      return;
    }
    
    if (isNaN(tasa) || tasa <= 0) {
      mostrarMensaje('error', 'Tasa de compra inválida');
      return;
    }

    try {
      const response = await iniciarDia({
        cripto_id: criptoId,
        capital_usd: capital,
        tasa_compra: tasa
      });
      
      mostrarMensaje('success', 
        `✅ Día iniciado\n\n` +
        `Cantidad: ${response.data.cantidad_cripto.toFixed(8)} cripto\n` +
        `Precio objetivo: $${response.data.precio_objetivo}\n` +
        `Precio equilibrio: $${response.data.precio_equilibrio}`
      );
      
      setCapitalUsd('');
      setTasaCompra('');
      fetchDia();
    } catch (error: any) {
      mostrarMensaje('error', error.response?.data?.detail || 'Error al iniciar día');
    }
  };

  const handleRegistrarVenta = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const precio = parseFloat(precioVenta);
    const cant = parseFloat(cantidad);
    
    if (isNaN(precio) || precio <= 0) {
      mostrarMensaje('error', 'Precio inválido');
      return;
    }
    
    if (isNaN(cant) || cant <= 0) {
      mostrarMensaje('error', 'Cantidad inválida');
      return;
    }

    // Validar contra precio de equilibrio
    if (dia && precio < dia.precio_equilibrio) {
      mostrarMensaje('error', 
        `⚠️ PRECIO PELIGROSO\n\n` +
        `El precio ${precio} está por debajo del equilibrio (${dia.precio_equilibrio}).\n` +
        `Esto causaría PÉRDIDA. Operación bloqueada.`
      );
      return;
    }

    try {
      const response = await registrarVenta({
        cantidad: cant,
        precio_venta: precio
      });
      
      mostrarMensaje('success', 
        `✅ Venta registrada\n\n` +
        `Monto neto: $${response.data.monto_neto}\n` +
        `Ganancia: $${response.data.ganancia}`
      );
      
      setPrecioVenta('');
      setCantidad('');
      fetchDia();
    } catch (error: any) {
      mostrarMensaje('error', error.response?.data?.detail || 'Error al registrar venta');
    }
  };

  const handleCerrarDia = async () => {
    if (!confirm('¿Cerrar el día actual? Esta acción no se puede deshacer.')) {
      return;
    }

    try {
      const response = await cerrarDia();
      mostrarMensaje('success', 
        `✅ Día cerrado\n\n` +
        `Capital final: $${response.data.capital_final}\n` +
        `Ganancia: $${response.data.ganancia}`
      );
      setDia(null);
      fetchDia();
    } catch (error: any) {
      mostrarMensaje('error', error.response?.data?.detail || 'Error al cerrar día');
    }
  };

  if (loading) return <div className="p-8">Cargando...</div>;

  // Vista: Sin día abierto
  if (!dia) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-8">Operaciones del Día</h1>
        
        {mensaje && (
          <div className={`mb-6 p-4 rounded-lg whitespace-pre-line ${
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
        
        {!hayCiclo && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <p className="text-yellow-700">
              ⚠️ No hay ciclo activo.<br/>
              Crea un ciclo en la sección <strong>Ciclo</strong> antes de operar.
            </p>
          </div>
        )}
        
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <h2 className="text-xl font-bold mb-4">Iniciar Nuevo Día</h2>
          
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <p className="text-blue-700 text-sm font-medium mb-2">💡 Cómo funciona:</p>
            <ol className="text-sm text-blue-600 list-decimal list-inside space-y-1">
              <li>Inviertes <strong>capital en USD</strong></li>
              <li>Compras cripto a una <strong>tasa</strong></li>
              <li>El sistema calcula cuánto cripto obtienes</li>
              <li>Te dice el <strong>precio objetivo</strong> para ganar 2%</li>
              <li>Publicas en P2P y registras ventas</li>
            </ol>
          </div>
          
          <form onSubmit={handleIniciarDia} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Criptomoneda</label>
              <select
                value={criptoId}
                onChange={(e) => setCriptoId(parseInt(e.target.value))}
                className="w-full px-4 py-2 border rounded"
                required
                disabled={!hayCiclo}
              >
                <option value={1}>USDT - Tether</option>
                <option value={2}>USDC - USD Coin</option>
                <option value={3}>BUSD - Binance USD</option>
                <option value={7}>DAI - Dai</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Capital en USD</label>
              <input
                type="number"
                step="0.01"
                value={capitalUsd}
                onChange={(e) => setCapitalUsd(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder="100.00"
                required
                disabled={!hayCiclo}
              />
              <p className="text-xs text-gray-500 mt-1">Cuántos dólares vas a invertir hoy</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Tasa de Compra (USD por cripto)</label>
              <input
                type="number"
                step="0.00000001"
                value={tasaCompra}
                onChange={(e) => setTasaCompra(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder="1.050"
                required
                disabled={!hayCiclo}
              />
              <p className="text-xs text-gray-500 mt-1">
                Precio al que compraste (Ej: si 1 USDT = $1.050, pon 1.050)
              </p>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
              disabled={!hayCiclo}
            >
              Iniciar Día
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Vista: Día abierto
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Día #{dia.numero_dia}</h1>
        <button
          onClick={handleCerrarDia}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Cerrar Día
        </button>
      </div>

      {mensaje && (
        <div className={`mb-6 p-4 rounded-lg whitespace-pre-line ${
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

      {/* Resumen del día */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Capital Invertido (USD)</h3>
          <p className="text-2xl font-bold">${dia.capital_usd.toLocaleString()}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Cantidad Comprada</h3>
          <p className="text-2xl font-bold">{dia.cantidad_cripto.toFixed(4)} {dia.cripto_simbolo}</p>
          <p className="text-xs text-gray-500">Tasa: ${dia.tasa_compra}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Precio Objetivo (2%)</h3>
          <p className="text-2xl font-bold text-green-600">${dia.precio_objetivo.toFixed(8)}</p>
          <p className="text-xs text-gray-500">Publica a este precio en P2P</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Precio Equilibrio</h3>
          <p className="text-2xl font-bold text-orange-600">${dia.precio_equilibrio.toFixed(8)}</p>
          <p className="text-xs text-red-500">⚠️ No vender debajo de esto</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Ganancia Acumulada</h3>
          <p className="text-3xl font-bold text-green-600">${dia.ganancia_neta.toFixed(2)}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm mb-2">Ventas Realizadas</h3>
          <p className="text-3xl font-bold">{dia.ventas_realizadas}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setVista('dia')}
          className={`px-4 py-2 rounded ${vista === 'dia' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Historial
        </button>
        <button
          onClick={() => setVista('ventas')}
          className={`px-4 py-2 rounded ${vista === 'ventas' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Registrar Venta
        </button>
      </div>

      {/* Vista Historial */}
      {vista === 'dia' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Historial de Ventas</h2>
          
          {ventas.length === 0 ? (
            <p className="text-gray-500">No hay ventas registradas</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">Hora</th>
                    <th className="px-4 py-2 text-left">Cantidad</th>
                    <th className="px-4 py-2 text-left">Precio</th>
                    <th className="px-4 py-2 text-left">Monto Neto</th>
                    <th className="px-4 py-2 text-left">Ganancia</th>
                  </tr>
                </thead>
                <tbody>
                  {ventas.map(v => (
                    <tr key={v.id} className="border-t">
                      <td className="px-4 py-2">{new Date(v.fecha).toLocaleTimeString()}</td>
                      <td className="px-4 py-2">{v.cantidad.toFixed(4)}</td>
                      <td className="px-4 py-2">${v.precio_venta.toFixed(8)}</td>
                      <td className="px-4 py-2">${v.monto_neto.toFixed(2)}</td>
                      <td className="px-4 py-2 text-green-600">${v.ganancia.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Vista Registrar Venta */}
      {vista === 'ventas' && (
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <h2 className="text-xl font-bold mb-4">Registrar Nueva Venta</h2>
          
          <form onSubmit={handleRegistrarVenta} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Precio de Venta</label>
              <input
                type="number"
                step="0.00000001"
                value={precioVenta}
                onChange={(e) => setPrecioVenta(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder={dia.precio_objetivo.toFixed(8)}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Objetivo: ${dia.precio_objetivo.toFixed(8)} | 
                Mínimo: ${dia.precio_equilibrio.toFixed(8)}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Cantidad Vendida</label>
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

            <button
              type="submit"
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
            >
              Registrar Venta
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
