import { useEffect, useState } from 'react';
import { getCicloActivo, crearCiclo, getBovedaResumen, getBovedaInventario } from '../../services/api';
import type { Ciclo, Criptomoneda } from '../../types';

export default function Ciclos() {
  const [ciclo, setCiclo] = useState<Ciclo | null>(null);
  const [loading, setLoading] = useState(true);
  const [capitalBoveda, setCapitalBoveda] = useState(0);
  const [inventarioBoveda, setInventarioBoveda] = useState<Criptomoneda[]>([]);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [vista, setVista] = useState<'info' | 'transferir'>('info');
  const [creando, setCreando] = useState(false);
  const [mensaje, setMensaje] = useState<{tipo: 'success' | 'error' | 'warning', texto: string} | null>(null);

  const fetchCiclo = async () => {
    try {
      const response = await getCicloActivo();
      setCiclo(response.data);
      setMostrarForm(false);
    } catch (error: any) {
      if (error.response?.status === 404) {
        setMostrarForm(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchBoveda = async () => {
    try {
      const [resumenRes, inventarioRes] = await Promise.all([
        getBovedaResumen(),
        getBovedaInventario()
      ]);
      setCapitalBoveda(resumenRes.data.capital_total_usd);
      setInventarioBoveda(inventarioRes.data);
    } catch (e) {
      setCapitalBoveda(0);
      setInventarioBoveda([]);
    }
  };

  useEffect(() => {
    const init = async () => {
      await fetchBoveda();
      await fetchCiclo();
    };
    init();
  }, []);

  const mostrarMensaje = (tipo: 'success' | 'error' | 'warning', texto: string) => {
    setMensaje({ tipo, texto });
    setTimeout(() => setMensaje(null), 8000);
  };

  const handleCrearCiclo = async () => {
    setCreando(true);
    const capitalInicial = capitalBoveda;

    try {
      await crearCiclo({ 
        capital_inicial: capitalInicial
      });
      
      if (capitalInicial === 0) {
        mostrarMensaje('warning', 
          '✅ Ciclo creado sin capital.\n\n' +
          '⚠️ IMPORTANTE: Para operar necesitas:\n' +
          '1. Ir a la sección BÓVEDA\n' +
          '2. Agregar criptomonedas\n' +
          '3. El capital se asignará automáticamente al ciclo'
        );
      } else {
        mostrarMensaje('success', `✅ Ciclo creado exitosamente con $${capitalInicial.toLocaleString()}`);
      }
      
      await fetchCiclo();
      await fetchBoveda();
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Error al crear ciclo';
      mostrarMensaje('error', detail);
    } finally {
      setCreando(false);
    }
  };

  if (loading) return <div className="p-8">Cargando...</div>;

  // Vista: Sin ciclo activo
  if (mostrarForm) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-8">Iniciar Nuevo Ciclo</h1>
        
        {/* Mensajes */}
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
        
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <p className="text-gray-600 mb-6">No hay ciclo activo. Crea uno para comenzar a operar.</p>
          
          {/* Capital de Bóveda */}
          <div className="bg-blue-50 p-4 rounded mb-6">
            <p className="font-medium mb-2">Capital disponible en bóveda:</p>
            <p className="text-3xl font-bold text-blue-600">${capitalBoveda.toLocaleString()}</p>
          </div>

          {capitalBoveda === 0 ? (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
              <p className="text-yellow-700 font-medium mb-2">⚠️ No hay capital en la bóveda</p>
              <p className="text-sm text-yellow-600 mb-3">
                Puedes crear el ciclo sin capital. Después deberás:
              </p>
              <ol className="text-sm text-yellow-700 list-decimal list-inside space-y-1">
                <li>Ir a la sección <strong>Bóveda</strong></li>
                <li>Agregar criptomonedas (USDT, BTC, etc.)</li>
                <li>El capital se asignará automáticamente al ciclo</li>
              </ol>
            </div>
          ) : (
            <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-6">
              <p className="text-green-700">
                ✅ Hay capital disponible. El ciclo se creará con ${capitalBoveda.toLocaleString()}.
              </p>
            </div>
          )}

          {/* Botón */}
          <button
            onClick={handleCrearCiclo}
            disabled={creando}
            className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 font-medium disabled:bg-gray-400"
          >
            {creando ? 'Creando...' : 
              capitalBoveda === 0 
                ? 'Crear Ciclo (sin capital por ahora)'
                : `Crear Ciclo con $${capitalBoveda.toLocaleString()}`
            }
          </button>
        </div>
      </div>
    );
  }

  if (!ciclo) return <div className="p-8">No hay ciclo activo</div>;

  // Vista: Ciclo activo
  const cicloSinCapital = ciclo.capital_inicial === 0;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Ciclo Activo #{ciclo.numero}</h1>

      {/* Mensajes */}
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

      {/* Alerta si no tiene capital */}
      {cicloSinCapital && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <p className="text-red-700 font-bold mb-2">⚠️ CICLO SIN CAPITAL</p>
          <p className="text-red-600 text-sm mb-3">
            Este ciclo no tiene capital asignado. No podrás operar hasta que agregues capital.
          </p>
          <p className="text-red-600 text-sm font-medium mb-2">
            Para agregar capital:
          </p>
          <ol className="text-sm text-red-600 list-decimal list-inside space-y-1">
            <li>Ve a la sección <strong>Bóveda</strong></li>
            <li>Agrega criptomonedas (USDT, BTC, etc.)</li>
            <li>El capital se asignará automáticamente a este ciclo</li>
          </ol>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setVista('info')}
          className={`px-4 py-2 rounded ${vista === 'info' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Información
        </button>
        <button
          onClick={() => setVista('transferir')}
          className={`px-4 py-2 rounded ${vista === 'transferir' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
        >
          Estado de Bóveda
        </button>
      </div>

      {/* Vista Información */}
      {vista === 'info' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm mb-2">Capital Inicial</h3>
              <p className={`text-2xl font-bold ${cicloSinCapital ? 'text-red-600' : ''}`}>
                ${ciclo.capital_inicial.toLocaleString()}
              </p>
              {cicloSinCapital && <p className="text-xs text-red-500 mt-1">Sin capital</p>}
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm mb-2">Ganancia Total</h3>
              <p className="text-2xl font-bold text-green-600">${(ciclo.ganancia_total || 0).toFixed(2)}</p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm mb-2">Rendimiento</h3>
              <p className="text-2xl font-bold">{(ciclo.rendimiento_porcentual || 0).toFixed(2)}%</p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm mb-2">Días Operados</h3>
              <p className="text-2xl font-bold">{ciclo.dias_operados}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold mb-4">Información del Ciclo</h2>
            <div className="space-y-2">
              <p><span className="font-medium">Fecha Inicio:</span> {ciclo.fecha_inicio}</p>
              <p><span className="font-medium">Estado:</span> <span className="px-2 py-1 bg-green-100 text-green-800 rounded">{ciclo.estado}</span></p>
              <p><span className="font-medium">Ventas Totales:</span> {ciclo.ventas_totales}</p>
            </div>
          </div>
        </>
      )}

      {/* Vista Estado de Bóveda */}
      {vista === 'transferir' && (
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
          <h2 className="text-xl font-bold mb-4">Estado de la Bóveda</h2>
          
          <div className="bg-blue-50 p-4 rounded mb-6">
            <p className="font-medium mb-2">Capital total en bóveda:</p>
            <p className="text-2xl font-bold text-blue-600">${capitalBoveda.toLocaleString()}</p>
          </div>

          {capitalBoveda === 0 ? (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <p className="text-yellow-700 font-medium mb-2">⚠️ No hay capital en la bóveda</p>
              <p className="text-yellow-600 text-sm">
                Ve a la sección <strong>Bóveda</strong> y agrega criptomonedas.<br/>
                El capital se asignará automáticamente a este ciclo.
              </p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h3 className="font-medium mb-3">Criptomonedas en Bóveda:</h3>
                <div className="space-y-2">
                  {inventarioBoveda.map(c => (
                    <div key={c.simbolo} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <div>
                        <p className="font-bold">{c.simbolo}</p>
                        <p className="text-sm text-gray-600">Cantidad: {c.cantidad}</p>
                      </div>
                      <p className="font-bold text-blue-600">${c.valor_usd.toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-green-50 border-l-4 border-green-400 p-4">
                <p className="text-green-700 text-sm">
                  ✅ Este capital está disponible para operaciones en el ciclo actual.
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
