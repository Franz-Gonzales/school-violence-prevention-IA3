import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getIncidents, getIncidentStats, getCameras } from '../utils/api';
import StatCard from '../components/ui/StatCard';
import IncidentCard from '../components/IncidentCard';
import Notification from '../components/Notification';

const Dashboard = () => {
    const navigate = useNavigate();
    const { user, logout, isAuthenticated } = useAuth();
    const [stats, setStats] = useState({
        alertasActivas: 0,
        incidentesHoy: 0,
        camarasActivas: 0,
        totalGrabado: '0 GB',
    });
    const [incidents, setIncidents] = useState([]);
    const [systemStatus, setSystemStatus] = useState('Operativo');
    const [notifications, setNotifications] = useState([]);

    // Obtener datos al montar el componente
    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        const fetchData = async () => {
            try {
                // Obtener estadísticas de incidentes
                const today = new Date();
                const startOfDay = new Date(today.setHours(0, 0, 0, 0)).toISOString();
                const endOfDay = new Date(today.setHours(23, 59, 59, 999)).toISOString();

                const incidentStats = await getIncidentStats(startOfDay, endOfDay);
                const recentIncidents = await getIncidents({ limite: 5 });
                const cameras = await getCameras(true);

                setStats({
                    alertasActivas: incidentStats.incidentes_activos || 0,
                    incidentesHoy: incidentStats.incidentes_hoy || 0,
                    camarasActivas: cameras.length,
                    totalGrabado: incidentStats.total_grabado || '0 GB',
                });
                setIncidents(recentIncidents);

                // Simular estado del sistema (podría venir de un endpoint)
                setSystemStatus('Operativo');
            } catch (error) {
                console.error('Error al cargar datos del dashboard:', error);
            }
        };

        fetchData();
    }, [isAuthenticated, navigate]);

    // Simulación de notificaciones (se integrará con WebSocket más adelante)
    useEffect(() => {
        // Simular una notificación para probar el componente
        setNotifications([
            {
                id: 1,
                message: 'Alerta de violencia - Se ha detectado un incidente en el Pasillo 2',
            },
        ]);
    }, []);

    const handleCloseNotification = (id) => {
        setNotifications(notifications.filter((notif) => notif.id !== id));
    };

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    if (!user) {
        return null;
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Encabezado */}
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <h1 className="text-2xl font-bold text-primary">SegurEscolar</h1>
                    <div className="flex items-center space-x-4">
                        <span className="text-gray-600">
                            Bienvenido, {user.nombre} ({user.rol})
                        </span>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </header>

            {/* Contenido Principal */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Notificaciones */}
                {notifications.map((notif) => (
                    <Notification
                        key={notif.id}
                        message={notif.message}
                        onClose={() => handleCloseNotification(notif.id)}
                    />
                ))}

                {/* Estadísticas */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                    <StatCard
                        title="Alertas Activas"
                        value={stats.alertasActivas}
                        color="text-red-600"
                        icon={<span>🚨</span>}
                    />
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
                    <StatCard
                        title="Total Grabado"
                        value={stats.totalGrabado}
                        color="text-blue-600"
                        icon={<span>💾</span>}
                    />
                </div>

                {/* Últimos Incidentes y Estado del Sistema */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Últimos Incidentes */}
                    <div className="lg:col-span-2">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            Últimos Incidentes
                        </h2>
                        <div className="space-y-4">
                            {incidents.length > 0 ? (
                                incidents.map((incident) => (
                                    <IncidentCard key={incident.id} incident={incident} />
                                ))
                            ) : (
                                <p className="text-gray-600">No hay incidentes recientes.</p>
                            )}
                        </div>
                    </div>

                    {/* Estado del Sistema */}
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
                                Última actualización:{' '}
                                {new Date().toLocaleTimeString()}
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;