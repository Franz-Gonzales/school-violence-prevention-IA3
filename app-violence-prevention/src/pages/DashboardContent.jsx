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
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
                <div className="p-8">
                    {/* Header profesional */}
                    <div className="bg-white rounded-2xl shadow-xl border border-blue-100 p-8 mb-8">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-800 to-indigo-800 bg-clip-text text-transparent">Panel de Control Educativo</h1>
                                <p className="text-gray-600 mt-1">Monitoreo y supervisión de seguridad en tiempo real</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-center py-16">
                        <div className="text-center">
                            <div className="relative mb-8">
                                <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="w-6 h-6 bg-blue-600 rounded-full animate-pulse"></div>
                                </div>
                            </div>
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">Cargando Panel de Control</h3>
                            <p className="text-gray-600">Obteniendo datos del sistema de seguridad...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
            <div className="p-8">
                
                {/* Header profesional con información institucional */}
                <div className="bg-white rounded-2xl shadow-xl border border-blue-100 p-8 mb-8 relative overflow-hidden">
                    {/* Background pattern */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full -translate-y-16 translate-x-16 opacity-50"></div>
                    <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-green-100 to-blue-100 rounded-full translate-y-12 -translate-x-12 opacity-50"></div>
                    
                    <div className="relative z-10">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-6">
                                <div className="p-4 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl shadow-lg">
                                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                </div>
                                <div>
                                    <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-800 to-indigo-800 bg-clip-text text-transparent">Panel de Control Educativo</h1>
                                    <p className="text-gray-600 mt-2 text-lg">Monitoreo y supervisión de seguridad en tiempo real</p>
                                    <div className="flex items-center space-x-4 mt-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-green-500">🏫</span>
                                            <span className="text-sm text-gray-600 font-medium">Centro Educativo Seguro</span>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                            <span className="text-sm text-gray-600 font-medium">Sistema Activo</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {/* Fecha y hora actual */}
                            <div className="text-right">
                                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                                    <div className="text-2xl font-bold text-blue-800">
                                        {new Date().toLocaleDateString('es-ES', { 
                                            day: '2-digit', 
                                            month: 'short',
                                            year: 'numeric'
                                        })}
                                    </div>
                                    <div className="text-sm text-gray-600 mt-1">
                                        {new Date().toLocaleDateString('es-ES', { 
                                            weekday: 'long'
                                        })}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-2 flex items-center justify-end space-x-1">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span>{new Date().toLocaleTimeString('es-ES', { 
                                            hour: '2-digit', 
                                            minute: '2-digit'
                                        })}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tarjetas de estadísticas mejoradas */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-8">
                    {/* Incidentes Hoy */}
                    <div className="bg-white rounded-2xl shadow-xl border border-orange-100 p-8 relative overflow-hidden group hover:shadow-2xl transition-all duration-300">
                        <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-orange-100 to-yellow-100 rounded-full -translate-y-10 translate-x-10 opacity-60 group-hover:scale-110 transition-transform duration-300"></div>
                        
                        <div className="relative z-10 flex items-center justify-between">
                            <div>
                                <div className="flex items-center space-x-3 mb-4">
                                    <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl shadow-lg">
                                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-800">Incidentes Detectados</h3>
                                        <p className="text-sm text-gray-600">En el día de hoy</p>
                                    </div>
                                </div>
                                
                                <div className="mb-4">
                                    <div className="text-4xl font-bold text-orange-600 mb-1">{stats.incidentesHoy}</div>
                                    {stats.incidentesHoy === 0 ? (
                                        <div className="flex items-center space-x-2">
                                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                            <span className="text-sm text-green-600 font-medium">Día sin incidentes</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center space-x-2">
                                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                                            <span className="text-sm text-orange-600 font-medium">Requiere atención</span>
                                        </div>
                                    )}
                                </div>
                                
                                <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-3 border border-orange-200">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-orange-800 font-semibold">Estado del día:</span>
                                        <span className={`text-xs font-bold ${stats.incidentesHoy === 0 ? 'text-green-700' : 'text-orange-700'}`}>
                                            {stats.incidentesHoy === 0 ? '✅ SEGURO' : '⚠️ ALERTA'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="text-6xl opacity-20">⚠️</div>
                        </div>
                    </div>

                    {/* Cámaras Activas */}
                    <div className="bg-white rounded-2xl shadow-xl border border-green-100 p-8 relative overflow-hidden group hover:shadow-2xl transition-all duration-300">
                        <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-green-100 to-blue-100 rounded-full -translate-y-10 translate-x-10 opacity-60 group-hover:scale-110 transition-transform duration-300"></div>
                        
                        <div className="relative z-10 flex items-center justify-between">
                            <div>
                                <div className="flex items-center space-x-3 mb-4">
                                    <div className="p-3 bg-gradient-to-br from-green-500 to-blue-500 rounded-xl shadow-lg">
                                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-800">Cámaras Operativas</h3>
                                        <p className="text-sm text-gray-600">Monitoreo activo</p>
                                    </div>
                                </div>
                                
                                <div className="mb-4">
                                    <div className="text-4xl font-bold text-green-600 mb-1">{stats.camarasActivas}</div>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                        <span className="text-sm text-green-600 font-medium">En línea y detectando</span>
                                    </div>
                                </div>
                                
                                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-3 border border-green-200">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-green-800 font-semibold">Cobertura:</span>
                                        <span className="text-xs text-green-700 font-bold">🎯 COMPLETA</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="text-6xl opacity-20">📹</div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Panel de incidentes */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center space-x-4">
                                    <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl">
                                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-gray-900">Registro de Incidentes</h2>
                                        <p className="text-gray-600">Eventos detectados en tiempo real</p>
                                    </div>
                                </div>
                                
                                {loading && (
                                    <div className="flex items-center text-sm text-blue-600">
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                                        Actualizando...
                                    </div>
                                )}
                                
                                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg px-4 py-2 border border-blue-200">
                                    <div className="text-sm font-semibold text-blue-800">
                                        {new Date().toLocaleDateString('es-ES', { 
                                            day: 'numeric', 
                                            month: 'long'
                                        })}
                                    </div>
                                </div>
                            </div>
                            
                            <div className="space-y-4">
                                {incidents.length > 0 ? (
                                    incidents.map((incident) => (
                                        <div key={incident.id} className="p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl border border-gray-200 hover:shadow-lg transition-all duration-300">
                                            <IncidentCard incident={incident} />
                                        </div>
                                    ))
                                ) : (
                                    <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-8 text-center border border-green-200">
                                        <div className="text-6xl mb-4">✅</div>
                                        <h3 className="text-xl font-bold text-green-800 mb-2">¡Excelente! Día sin incidentes</h3>
                                        <p className="text-green-700 font-medium mb-4">
                                            No se han detectado eventos de seguridad en el día de hoy.
                                        </p>
                                        <div className="bg-white rounded-lg p-4 border border-green-200">
                                            <div className="flex items-center justify-center space-x-3 text-sm text-green-600">
                                                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                                <span className="font-semibold">Sistema de IA monitoreando activamente</span>
                                                <span className="text-green-500">🛡️</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Panel de estado del sistema */}
                    <div className="space-y-6">
                        {/* Estado general */}
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Estado del Sistema</h3>
                            </div>
                            
                            <div className="text-center py-4">
                                <div className={`text-3xl font-bold mb-2 ${
                                    systemStatus === 'Operativo' ? 'text-green-600' : 'text-red-600'
                                }`}>
                                    {systemStatus}
                                </div>
                                <p className="text-sm text-gray-600 mb-4">
                                    Última actualización: {new Date().toLocaleTimeString()}
                                </p>
                                
                                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
                                    <div className="flex items-center justify-center space-x-2 text-sm text-green-700">
                                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                        <span className="font-semibold">Actualización automática cada 30s</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Resumen de seguridad */}
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Resumen de Seguridad</h3>
                            </div>
                            
                            <div className="space-y-4">
                                <div className="flex justify-between items-center p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                    <span className="text-sm font-medium text-gray-700">Incidentes Hoy:</span>
                                    <span className={`font-bold ${stats.incidentesHoy === 0 ? 'text-green-600' : 'text-orange-600'}`}>
                                        {stats.incidentesHoy}
                                    </span>
                                </div>
                                
                                <div className="flex justify-between items-center p-3 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                                    <span className="text-sm font-medium text-gray-700">Cámaras Activas:</span>
                                    <span className="font-bold text-green-600">{stats.camarasActivas}</span>
                                </div>
                                
                                {stats.incidentesHoy === 0 && (
                                    <div className="bg-gradient-to-r from-green-100 to-emerald-100 rounded-lg p-4 border border-green-300">
                                        <div className="flex items-center space-x-2 text-green-800">
                                            <span className="text-lg">🏆</span>
                                            <div>
                                                <div className="text-sm font-bold">¡Día Ejemplar!</div>
                                                <div className="text-xs">Ambiente educativo seguro</div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Panel de monitoreo activo */}
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Monitoreo Activo</h3>
                            </div>
                            
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                        <span className="text-sm font-medium text-gray-700">Detección IA:</span>
                                    </div>
                                    <span className="text-sm font-bold text-green-600">ACTIVA</span>
                                </div>
                                
                                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                                        <span className="text-sm font-medium text-gray-700">Alertas:</span>
                                    </div>
                                    <span className="text-sm font-bold text-blue-600">HABILITADAS</span>
                                </div>
                                
                                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                                        <span className="text-sm font-medium text-gray-700">Grabación:</span>
                                    </div>
                                    <span className="text-sm font-bold text-purple-600">AUTO</span>
                                </div>
                                
                                {/* Indicador de rendimiento */}
                                <div className="mt-4 p-3 bg-gradient-to-r from-gray-50 to-slate-50 rounded-lg border border-gray-200">
                                    <div className="text-center">
                                        <div className="text-xs text-gray-600 mb-2 font-semibold">Rendimiento del Sistema</div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full w-[95%] animate-pulse"></div>
                                        </div>
                                        <div className="text-xs text-green-600 mt-1 font-bold">95% Óptimo</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardContent;