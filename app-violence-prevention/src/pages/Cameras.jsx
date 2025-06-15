import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/ui/Card';
import { getCameras } from '../utils/api';

const Cameras = () => {
    const navigate = useNavigate();
    const [cameras, setCameras] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCameras = async () => {
            try {
                const data = await getCameras(false); // Solo cámaras activas
                setCameras(data);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };
        fetchCameras();
    }, []);

    const getStatusIcon = (estado) => {
        switch (estado) {
            case 'activa':
                return { icon: '🟢', color: 'text-green-600', bg: 'bg-green-100', border: 'border-green-300' };
            case 'inactiva':
                return { icon: '🔴', color: 'text-red-600', bg: 'bg-red-100', border: 'border-red-300' };
            case 'mantenimiento':
                return { icon: '🟡', color: 'text-yellow-600', bg: 'bg-yellow-100', border: 'border-yellow-300' };
            default:
                return { icon: '⚫', color: 'text-gray-600', bg: 'bg-gray-100', border: 'border-gray-300' };
        }
    };

    const getLocationIcon = (ubicacion) => {
        const location = ubicacion.toLowerCase();
        if (location.includes('patio') || location.includes('recreo')) return '🏃‍♂️';
        if (location.includes('aula') || location.includes('salon')) return '📚';
        if (location.includes('pasillo') || location.includes('corredor')) return '🚶‍♂️';
        if (location.includes('entrada') || location.includes('acceso')) return '🚪';
        if (location.includes('biblioteca')) return '📖';
        if (location.includes('laboratorio')) return '🔬';
        if (location.includes('gimnasio') || location.includes('deportes')) return '🏃‍♀️';
        if (location.includes('cafeteria') || location.includes('comedor')) return '🍽️';
        return '🏫';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
                <div className="p-8">
                    {/* Header profesional */}
                    <div className="bg-white rounded-2xl shadow-xl border border-blue-100 p-8 mb-8">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-gradient-to-br from-green-600 to-blue-600 rounded-xl">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold bg-gradient-to-r from-green-800 to-blue-800 bg-clip-text text-transparent">Sistema de Cámaras Educativas</h1>
                                <p className="text-gray-600 mt-1">Monitoreo integral del centro educativo</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-center py-16">
                        <div className="text-center">
                            <div className="relative mb-8">
                                <div className="animate-spin rounded-full h-16 w-16 border-4 border-green-200 border-t-green-600 mx-auto"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="w-6 h-6 bg-green-600 rounded-full animate-pulse"></div>
                                </div>
                            </div>
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">Cargando Sistema de Cámaras</h3>
                            <p className="text-gray-600">Obteniendo información de las cámaras de seguridad...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-pink-50">
                <div className="p-8">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-white rounded-2xl shadow-xl border border-red-200 p-8 text-center">
                            <div className="text-red-600 text-6xl mb-6">⚠️</div>
                            <h1 className="text-2xl font-bold text-gray-900 mb-4">Error en el Sistema de Cámaras</h1>
                            <p className="text-red-600 mb-6 font-medium">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all transform hover:scale-105 shadow-lg font-semibold"
                            >
                                🔄 Reintentar Conexión
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
            <div className="p-8">
                
                {/* Header profesional con estadísticas */}
                <div className="bg-white rounded-2xl shadow-xl border border-blue-100 p-8 mb-8 relative overflow-hidden">
                    {/* Background decorativo */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-green-100 to-blue-100 rounded-full -translate-y-16 translate-x-16 opacity-50"></div>
                    <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-blue-100 to-indigo-100 rounded-full translate-y-12 -translate-x-12 opacity-50"></div>
                    
                    <div className="relative z-10">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-6">
                                <div className="p-4 bg-gradient-to-br from-green-600 to-blue-600 rounded-2xl shadow-lg">
                                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <div>
                                    <h1 className="text-4xl font-bold bg-gradient-to-r from-green-800 to-blue-800 bg-clip-text text-transparent">Sistema de Vigilancia Educativa</h1>
                                    <p className="text-gray-600 mt-2 text-lg">Monitoreo integral y protección del centro educativo</p>
                                    <div className="flex items-center space-x-4 mt-3">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-green-500">🏫</span>
                                            <span className="text-sm text-gray-600 font-medium">Cobertura Total del Plantel</span>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                            <span className="text-sm text-gray-600 font-medium">Monitoreo en Tiempo Real</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {/* Estadísticas rápidas */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 text-center border border-green-200">
                                    <div className="text-2xl font-bold text-green-600">
                                        {cameras.filter(cam => cam.estado === 'activa').length}
                                    </div>
                                    <div className="text-xs text-green-700 font-semibold">Activas</div>
                                </div>
                                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 text-center border border-blue-200">
                                    <div className="text-2xl font-bold text-blue-600">{cameras.length}</div>
                                    <div className="text-xs text-blue-700 font-semibold">Total</div>
                                </div>
                                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 text-center border border-purple-200">
                                    <div className="text-2xl font-bold text-purple-600">AI</div>
                                    <div className="text-xs text-purple-700 font-semibold">Detección</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {cameras.length > 0 ? (
                    <>
                        {/* Resumen de estado */}
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-8">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl">
                                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-gray-900">Estado General del Sistema</h2>
                                        <p className="text-gray-600">Resumen operativo de las cámaras de seguridad</p>
                                    </div>
                                </div>
                                
                                <div className="flex items-center space-x-4">
                                    {cameras.filter(cam => cam.estado === 'activa').length === cameras.length ? (
                                        <div className="flex items-center space-x-2 bg-green-50 px-4 py-2 rounded-full border border-green-200">
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                            <span className="text-green-700 font-semibold text-sm">✅ Sistema Óptimo</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center space-x-2 bg-yellow-50 px-4 py-2 rounded-full border border-yellow-200">
                                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                                            <span className="text-yellow-700 font-semibold text-sm">⚠️ Atención Requerida</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Grid de cámaras mejorado */}
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                            {cameras.map((camera) => {
                                const status = getStatusIcon(camera.estado);
                                const locationIcon = getLocationIcon(camera.ubicacion);
                                
                                return (
                                    <div key={camera.id} className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 group">
                                        {/* Header de la cámara */}
                                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 relative overflow-hidden">
                                            <div className="absolute top-0 right-0 w-20 h-20 bg-white opacity-10 rounded-full -translate-y-10 translate-x-10"></div>
                                            
                                            <div className="relative z-10 flex items-center justify-between">
                                                <div className="flex items-center space-x-3">
                                                    <div className="text-2xl">{locationIcon}</div>
                                                    <div>
                                                        <h3 className="text-lg font-bold text-white">{camera.nombre}</h3>
                                                        <p className="text-blue-100 text-sm">ID: CAM-{String(camera.id).padStart(3, '0')}</p>
                                                    </div>
                                                </div>
                                                
                                                <div className={`px-3 py-1 rounded-full text-xs font-bold ${status.bg} ${status.color} ${status.border} border flex items-center space-x-1`}>
                                                    <span>{status.icon}</span>
                                                    <span>{camera.estado.toUpperCase()}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Vista previa del video */}
                                        <div className="relative h-48 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center group-hover:from-gray-700 group-hover:to-gray-800 transition-all duration-300">
                                            {camera.estado === 'activa' ? (
                                                <>
                                                    {/* Simulación de stream en vivo */}
                                                    <div className="absolute inset-4 border-2 border-dashed border-gray-600 rounded-lg flex items-center justify-center">
                                                        <div className="text-center text-gray-400">
                                                            <div className="text-4xl mb-2">📹</div>
                                                            <p className="text-sm font-medium">Vista Previa en Vivo</p>
                                                            <p className="text-xs opacity-75">Haga clic para ver detalles</p>
                                                        </div>
                                                    </div>
                                                    
                                                    {/* Indicador de transmisión en vivo */}
                                                    <div className="absolute top-4 left-4 bg-red-500 px-2 py-1 rounded-full text-white text-xs font-bold flex items-center space-x-1 animate-pulse">
                                                        <div className="w-2 h-2 bg-white rounded-full"></div>
                                                        <span>EN VIVO</span>
                                                    </div>
                                                    
                                                    {/* Información técnica */}
                                                    <div className="absolute bottom-4 right-4 bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs">
                                                        {camera.resolucion_ancho}x{camera.resolucion_alto} | {camera.fps}fps
                                                    </div>
                                                </>
                                            ) : (
                                                <div className="text-center text-gray-500">
                                                    <div className="text-4xl mb-2">📴</div>
                                                    <p className="text-sm font-medium">Cámara {camera.estado}</p>
                                                    <p className="text-xs">No hay señal disponible</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* Información de la cámara */}
                                        <div className="p-6">
                                            <div className="space-y-4">
                                                {/* Ubicación */}
                                                <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                                    <div className="text-blue-500">📍</div>
                                                    <div>
                                                        <div className="text-sm font-semibold text-gray-800">Ubicación</div>
                                                        <div className="text-sm text-blue-700 font-medium">{camera.ubicacion}</div>
                                                    </div>
                                                </div>

                                                {/* Especificaciones técnicas */}
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div className="text-center p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                                        <div className="text-green-600 font-bold text-lg">{camera.tipo_camara.toUpperCase()}</div>
                                                        <div className="text-xs text-green-700 font-semibold">Tipo</div>
                                                    </div>
                                                    <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                                        <div className="text-purple-600 font-bold text-lg">{camera.fps}</div>
                                                        <div className="text-xs text-purple-700 font-semibold">FPS</div>
                                                    </div>
                                                </div>

                                                {/* Última actividad */}
                                                <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-gray-50 to-slate-50 rounded-lg border border-gray-200">
                                                    <div className="text-gray-500">⏰</div>
                                                    <div>
                                                        <div className="text-sm font-semibold text-gray-800">Última Actividad</div>
                                                        <div className="text-xs text-gray-600">
                                                            {new Date(camera.ultima_actividad).toLocaleString('es-ES')}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Botón de acción */}
                                            <button
                                                onClick={() => navigate(`/cameras/${camera.id}`)}
                                                className={`mt-6 w-full py-3 px-4 rounded-xl font-bold text-white transition-all duration-300 transform hover:scale-[1.02] shadow-lg hover:shadow-xl ${
                                                    camera.estado === 'activa' 
                                                        ? 'bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700' 
                                                        : 'bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700'
                                                }`}
                                            >
                                                <div className="flex items-center justify-center space-x-2">
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                    </svg>
                                                    <span>
                                                        {camera.estado === 'activa' ? 'Ver Transmisión' : 'Ver Detalles'}
                                                    </span>
                                                </div>
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </>
                ) : (
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-12 text-center">
                            <div className="text-6xl mb-6">📹</div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">Sistema de Cámaras No Configurado</h2>
                            <p className="text-gray-600 mb-6 text-lg">
                                No hay cámaras registradas en el sistema educativo.
                            </p>
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                                <p className="text-sm text-blue-800 font-medium">
                                    🔧 Contacta al administrador del sistema para configurar las cámaras de seguridad del centro educativo.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Cameras;