import { useState } from 'react'
import Dashboard from './components/dashboard/Dashboard'
import Boveda from './components/boveda/Boveda'
import Ciclos from './components/ciclos/Ciclos'
import Operaciones from './components/operaciones/Operaciones'

function App() {
  const [vista, setVista] = useState<'ciclos' | 'dashboard' | 'boveda' | 'operaciones'>('ciclos')

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navegación */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-4 py-4">
            <button
              onClick={() => setVista('ciclos')}
              className={`px-4 py-2 rounded ${vista === 'ciclos' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Ciclo
            </button>
            <button
              onClick={() => setVista('dashboard')}
              className={`px-4 py-2 rounded ${vista === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setVista('boveda')}
              className={`px-4 py-2 rounded ${vista === 'boveda' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Bóveda
            </button>
            <button
              onClick={() => setVista('operaciones')}
              className={`px-4 py-2 rounded ${vista === 'operaciones' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Operaciones
            </button>
          </div>
        </div>
      </nav>

      {/* Contenido */}
      {vista === 'ciclos' && <Ciclos />}
      {vista === 'dashboard' && <Dashboard />}
      {vista === 'boveda' && <Boveda />}
      {vista === 'operaciones' && <Operaciones />}
    </div>
  )
}

export default App
