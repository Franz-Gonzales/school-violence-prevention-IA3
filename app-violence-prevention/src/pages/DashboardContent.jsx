import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getIncidents, getIncidentStats, getCameras } from '../utils/api';
import StatCard from '../components/ui/StatCard';
import IncidentCard from '../components/IncidentCard';

const DashboardContent = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [stats, setStats] = useState({
        incidentesHoy: 0,
        camarasActivas: 0,
    });
    const [incidents, setIncidents] = useState([]);
    const [systemStatus, setSystemStatus] = useState('Operativo');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        fetchData();
        
        // Actualizar datos cada 30 segundos para tiempo real
        const interval = setInterval(fetchData, 30000);
        
        return () => clearInterval(interval);
    }, [isAuthenticated, navigate]);

    const fetchData = async () => {
        try {
            setLoading(true);
            
            // *** CORREGIDO: Obtener solo fecha de HOY (día actual) ***
            const today = new Date();
            const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0, 0);
            const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999);
            
            console.log('📅 Filtrando incidentes de HOY:', {
                inicio: startOfDay.toISOString(),
                fin: endOfDay.toISOString(),
                fecha_actual: today.toLocaleDateString()
            });

            // Ejecutar todas las consultas en paralelo
            const [incidentStats, todayIncidents, cameras] = await Promise.all([
                // Estadísticas de incidentes de hoy
                getIncidentStats(startOfDay.toISOString(), endOfDay.toISOString()),
                
                // *** INCIDENTES SOLO DEL DÍA ACTUAL ***
                getIncidents({ 
                    fecha_inicio: startOfDay.toISOString(),
                    fecha_fin: endOfDay.toISOString(),
                    limite: 10 // Máximo 10 incidentes del día
                }),
                
                // Cámaras activas
                getCameras(true)
            ]);

            // Verificar que los incidentes sean realmente de hoy
            const incidentesHoyFiltrados = todayIncidents.filter(incident => {
                const incidentDate = new Date(incident.fecha_hora_inicio);
                const incidentDay = new Date(incidentDate.getFullYear(), incidentDate.getMonth(), incidentDate.getDate());
                const todayDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
                return incidentDay.getTime() === todayDay.getTime();
            });

            console.log(`📊 Incidentes encontrados de hoy: ${incidentesHoyFiltrados.length}`, {
                total_consultados: todayIncidents.length,
                filtrados_hoy: incidentesHoyFiltrados.length,
                estadisticas_hoy: incidentStats.total_incidentes
            });

            // Actualizar estadísticas con datos reales
            setStats({
                incidentesHoy: incidentStats.total_incidentes || 0,
                camarasActivas: cameras.length || 0,
            });
            
            // *** SOLO MOSTRAR INCIDENTES DE HOY ***
            setIncidents(incidentesHoyFiltrados || []);
            setSystemStatus('Operativo');
            
        } catch (error) {
            console.error('❌ Error al cargar datos del dashboard:', error);
            setSystemStatus('Error en conexión');
            
            // En caso de error, mantener los valores anteriores o usar 0
            setStats(prevStats => ({
                incidentesHoy: prevStats.incidentesHoy || 0,
                camarasActivas: prevStats.camarasActivas || 0,
            }));
            
            // Limpiar incidentes en caso de error
            setIncidents([]);
        } finally {
            setLoading(false);
        }
    };

    if (loading && stats.incidentesHoy === 0 && stats.camarasActivas === 0) {
        return (
            <div className="py-6">
                <h1 className="text-2xl font-bold text-primary mb-4">Dashboard</h1>
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-2 text-gray-600">Cargando datos del dashboard...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="py-6">
            <h1 className="text-2xl font-bold text-primary mb-4">Dashboard</h1>

            {/* Solo mostrar las 2 tarjetas de estadísticas solicitadas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                <StatCard
                    title="Incidentes Hoy"
                    value={stats.incidentesHoy}
                    color="text-yellow-600"
                    icon={<span>⚠️</span>}
                />
                <StatCard
                    title="Cámaras Activas"
                    value={stats.camarasActivas}
                    color="text-green-600"
                    icon={<span>📹</span>}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-gray-900">
                            Incidentes de Hoy
                        </h2>
                        {loading && (
                            <div className="flex items-center text-sm text-gray-500">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
                                Actualizando...
                            </div>
                        )}
                        {/* Mostrar fecha actual */}
                        <div className="text-sm text-gray-500">
                            {new Date().toLocaleDateString('es-ES', { 
                                weekday: 'long', 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                            })}
                        </div>
                    </div>
                    <div className="space-y-4">
                        {incidents.length > 0 ? (
                            incidents.map((incident) => (
                                <IncidentCard key={incident.id} incident={incident} />
                            ))
                        ) : (
                            <div className="bg-white rounded-lg shadow-md p-6 text-center">
                                <div className="text-4xl mb-3">✅</div>
                                <p className="text-gray-600 font-medium">No hay incidentes registrados hoy.</p>
                                <p className="text-sm text-gray-500 mt-2">
                                    {stats.incidentesHoy === 0 
                                        ? "¡Excelente! No se han detectado incidentes en el día de hoy."
                                        : "Los incidentes de hoy aparecerán aquí automáticamente."
                                    }
                                </p>
                                {/* Indicador de tiempo real */}
                                <div className="mt-4 flex items-center justify-center text-xs text-gray-400">
                                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                                    Sistema monitoreando en tiempo real
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                        Estado del Sistema
                    </h2>
                    <div className="bg-white rounded-lg shadow-md p-6 text-center">
                        <p
                            className={`text-2xl font-bold ${
                                systemStatus === 'Operativo'
                                    ? 'text-green-600'
                                    : 'text-red-600'
                            }`}
                        >
                            {systemStatus}
                        </p>
                        <p className="text-sm text-gray-600 mt-2">
                            Última actualización: {new Date().toLocaleTimeString()}
                        </p>
                        
                        {/* Indicador de tiempo real */}
                        <div className="mt-3 flex items-center justify-center text-xs text-gray-500">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                            Actualización automática cada 30s
                        </div>
                    </div>
                    
                    {/* Resumen rápido adicional */}
                    <div className="bg-white rounded-lg shadow-md p-4 mt-4">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Resumen de Hoy</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Incidentes:</span>
                                <span className={`font-medium ${stats.incidentesHoy === 0 ? 'text-green-600' : 'text-yellow-600'}`}>
                                    {stats.incidentesHoy}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Cámaras:</span>
                                <span className="font-medium text-green-600">{stats.camarasActivas} activas</span>
                            </div>
                            {stats.incidentesHoy === 0 && (
                                <div className="mt-3 p-2 bg-green-50 rounded-lg">
                                    <div className="flex items-center text-xs text-green-700">
                                        <span className="mr-2">🛡️</span>
                                        Día sin incidentes
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Estado de monitoreo */}
                    <div className="bg-white rounded-lg shadow-md p-4 mt-4">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Monitoreo Activo</h3>
                        <div className="space-y-2 text-xs">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Detección IA:</span>
                                <span className="flex items-center text-green-600">
                                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-1"></div>
                                    Activa
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Alertas:</span>
                                <span className="text-blue-600">Configuradas</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Grabación:</span>
                                <span className="text-blue-600">Automática</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardContent;