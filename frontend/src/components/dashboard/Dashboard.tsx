import { useEffect, useState } from 'react';
import { getDashboardResumen } from '../../services/api';
import type { DashboardData } from '../../types';

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getDashboardResumen();
        setData(response.data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8">Cargando...</div>;
  if (!data) return <div className="p-8">Error al cargar datos</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard P2P</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Capital Total" value={`$${data.capital_total.toLocaleString()}`} />
        <MetricCard title="Ventas Hoy" value={data.ventas_hoy} />
        <MetricCard title="Ganancia Total" value={`$${data.ganancia_total.toFixed(2)}`} />
        <MetricCard title="Ciclos Completados" value={data.ciclos_completados} />
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-gray-500 text-sm mb-2">{title}</h3>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
