import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCameras, api } from '../utils/api';
import WebRTCClient from '../utils/webrtc';

const CameraDetail = () => {
    const { cameraId } = useParams();
    const navigate = useNavigate();
    const videoRef = useRef(null);
    const webRTCClientRef = useRef(null);
    const notificationSoundRef = useRef(null);

    const [cameraDetail, setCameraDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Estados del sistema MEJORADOS
    const [systemState, setSystemState] = useState({
        camera: 'inactive',      // inactive, connecting, active, error
        stream: 'disconnected',  // disconnected, connecting, connected, streaming, error
        detection: 'inactive',   // inactive, starting, active, stopping, error
        connection: 'disconnected' // disconnected, connecting, connected, error, buffering
    });

    // Estados de la detección
    const [detectionData, setDetectionData] = useState({
        isActive: false,
        lastDetection: null,
        violenceAlert: null,
        peopleCount: 0,
        confidence: 0
    });

    // Configuraciones
    const [settings, setSettings] = useState({
        streamQuality: 'Alta',
        autoRecord: true,
        soundAlerts: true,
        sensitivity: 'Media'
    });

    // Estadísticas en tiempo real
    const [stats, setStats] = useState({
        frameRate: 0,
        bandwidth: 0,
        uptime: 0,
        totalAlerts: 0
    });

    // Notificaciones
    const [notifications, setNotifications] = useState([]);

    // Cleanup function mejorada
    const cleanup = useCallback(() => {
        if (webRTCClientRef.current) {
            console.log('🧹 Limpiando recursos WebRTC...');
            webRTCClientRef.current.stop();
            webRTCClientRef.current = null;
        }

        setSystemState(prev => ({
            ...prev,
            stream: 'disconnected',
            detection: 'inactive',
            connection: 'disconnected'
        }));

        setDetectionData({
            isActive: false,
            lastDetection: null,
            violenceAlert: null,
            peopleCount: 0,
            confidence: 0
        });
    }, []);

    // Agregar notificación
    const addNotification = useCallback((type, message, data = {}) => {
        const notification = {
            id: Date.now() + Math.random(),
            type, // 'info', 'warning', 'error', 'violence'
            message,
            timestamp: new Date(),
            data,
            read: false
        };

        setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Mantener solo 10

        // Auto-remover después de cierto tiempo
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== notification.id));
        }, type === 'violence' ? 15000 : 5000);

        // Reproducir sonido si está habilitado
        if (settings.soundAlerts && (type === 'violence' || type === 'error')) {
            playNotificationSound(type);
        }
    }, [settings.soundAlerts]);

    // Reproducir sonido de notificación
    const playNotificationSound = useCallback((type) => {
        if (!notificationSoundRef.current) {
            notificationSoundRef.current = new Audio();
        }

        // Diferentes sonidos para diferentes tipos
        const soundUrls = {
            violence: '/sounds/alert-critical.mp3',
            error: '/sounds/alert-error.mp3',
            info: '/sounds/notification.mp3'
        };

        notificationSoundRef.current.src = soundUrls[type] || soundUrls.info;
        notificationSoundRef.current.play().catch(e =>
            console.log('No se pudo reproducir sonido:', e)
        );
    }, []);

    useEffect(() => {
        const fetchCamera = async () => {
            try {
                setLoading(true);
                const cameras = await getCameras();
                const camera = cameras.find(cam => cam.id === Number(cameraId));

                if (!camera) {
                    throw new Error('Cámara no encontrada');
                }

                setCameraDetail(camera);
                // CORREGIR: Actualizar estado de cámara según estado real
                setSystemState(prev => ({
                    ...prev,
                    camera: camera.estado === 'activa' ? 'active' : 'inactive'
                }));

                addNotification('info', `Cámara ${camera.nombre} cargada correctamente`);

            } catch (err) {
                setError(err.message);
                addNotification('error', `Error al cargar cámara: ${err.message}`);
            } finally {
                setLoading(false);
            }
        };

        fetchCamera();
        return cleanup;
    }, [cameraId, cleanup, addNotification]);

    // Configurar video element para mejor rendimiento
    useEffect(() => {
        if (videoRef.current) {
            const video = videoRef.current;

            video.playsInline = true;
            video.muted = true;
            video.autoplay = true;
            video.controls = false;

            const handleVideoEvent = (eventType, status) => {
                console.log(`📹 Video evento: ${eventType}`);

                const statusMap = {
                    'loadstart': 'connecting',
                    'loadedmetadata': 'connected',
                    'canplay': 'connected',
                    'playing': 'streaming',
                    'stalled': 'buffering',
                    'waiting': 'buffering',
                    'error': 'error'
                };

                setSystemState(prev => ({
                    ...prev,
                    connection: statusMap[eventType] || prev.connection
                }));

                if (eventType === 'loadedmetadata') {
                    addNotification('info', `Video conectado: ${video.videoWidth}x${video.videoHeight}`);
                } else if (eventType === 'error') {
                    addNotification('error', 'Error en la conexión de video');
                }
            };

            // Eventos del video
            video.addEventListener('loadstart', () => handleVideoEvent('loadstart'));
            video.addEventListener('loadedmetadata', () => handleVideoEvent('loadedmetadata'));
            video.addEventListener('canplay', () => handleVideoEvent('canplay'));
            video.addEventListener('playing', () => handleVideoEvent('playing'));
            video.addEventListener('stalled', () => handleVideoEvent('stalled'));
            video.addEventListener('waiting', () => handleVideoEvent('waiting'));
            video.addEventListener('error', () => handleVideoEvent('error'));
        }
    }, [addNotification]);

    // Manejo de detección mejorado CORREGIDO
    const handleDetection = useCallback((data) => {
        console.log('🔍 Datos de detección recibidos:', data);

        setDetectionData(prev => ({
            ...prev,
            lastDetection: new Date(),
            peopleCount: data.personas_detectadas || 0,
            confidence: data.probabilidad || 0
        }));

        if (data.violencia_detectada) {
            const alertData = {
                probability: data.probabilidad || 0, // CORREGIR: Usar probabilidad real
                peopleCount: data.personas_detectadas || 0,
                timestamp: new Date(),
                cameraId: cameraId,
                location: cameraDetail?.ubicacion
            };

            setDetectionData(prev => ({
                ...prev,
                violenceAlert: alertData
            }));

            // Notificación crítica CON PROBABILIDAD CORRECTA
            const probabilidadPorcentaje = ((data.probabilidad || 0) * 100).toFixed(1);
            addNotification(
                'violence',
                `🚨 VIOLENCIA DETECTADA - Probabilidad: ${probabilidadPorcentaje}%`,
                alertData
            );

            // Efecto visual de alerta
            if (videoRef.current) {
                videoRef.current.style.border = '4px solid #ff0000';
                videoRef.current.style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.7)';

                setTimeout(() => {
                    if (videoRef.current) {
                        videoRef.current.style.border = 'none';
                        videoRef.current.style.boxShadow = 'none';
                    }
                }, 3000);
            }

            setStats(prev => ({ ...prev, totalAlerts: prev.totalAlerts + 1 }));
        }
    }, [cameraId, cameraDetail?.ubicacion, addNotification]);

    const handleToggleStream = async () => {
        try {
            if (systemState.stream === 'disconnected') {
                console.log('🎥 Iniciando stream...');
                setSystemState(prev => ({ ...prev, stream: 'connecting' }));
                addNotification('info', 'Iniciando conexión de video...');

                // CORREGIR: Activar cámara y actualizar estado
                await api.post(`/api/v1/cameras/${cameraId}/activar`);
                setSystemState(prev => ({ ...prev, camera: 'active' }));

                // Crear nuevo cliente WebRTC
                const client = new WebRTCClient(cameraId, videoRef.current, handleDetection);
                webRTCClientRef.current = client;

                // Conectar sin detección inicialmente
                await client.connect(false);
                setSystemState(prev => ({ ...prev, stream: 'connected' }));
                addNotification('info', 'Stream de video iniciado correctamente');

            } else {
                console.log('🛑 Deteniendo stream...');
                setSystemState(prev => ({ ...prev, stream: 'connecting' }));
                addNotification('info', 'Deteniendo stream...');

                // CORREGIR: Desactivar cámara y actualizar estado
                await api.post(`/api/v1/cameras/${cameraId}/desactivar`);
                setSystemState(prev => ({ ...prev, camera: 'inactive' }));

                // Limpiar cliente WebRTC
                cleanup();
                addNotification('info', 'Stream detenido correctamente');
            }
        } catch (err) {
            console.error('❌ Error al manejar stream:', err);
            setError(`Error al manejar stream: ${err.message}`);
            addNotification('error', `Error en stream: ${err.message}`);
            setSystemState(prev => ({ ...prev, stream: 'error', camera: 'error' }));
            cleanup();
        }
    };

    const handleToggleDetection = async () => {
        if (!webRTCClientRef.current) {
            addNotification('error', 'Debe iniciar el stream primero.');
            return;
        }

        try {
            if (!detectionData.isActive) {
                console.log('🔍 Activando detección...');
                setSystemState(prev => ({ ...prev, detection: 'starting' }));
                addNotification('info', 'Iniciando detección de violencia...');

                // Activar cámara en el backend si no está activa
                if (systemState.camera !== 'active') {
                    await api.post(`/api/v1/cameras/${cameraId}/activar`);
                    setSystemState(prev => ({ ...prev, camera: 'active' }));
                }

                // Activar detección en el cliente WebRTC
                webRTCClientRef.current.toggleDetection(true);
                setDetectionData(prev => ({ ...prev, isActive: true }));
                setSystemState(prev => ({ ...prev, detection: 'active' }));
                addNotification('info', '🔍 Detección de violencia activada');

            } else {
                console.log('⏹️ Desactivando detección...');
                setSystemState(prev => ({ ...prev, detection: 'stopping' }));
                addNotification('info', 'Deteniendo detección...');

                // Desactivar detección en el cliente WebRTC
                webRTCClientRef.current.toggleDetection(false);
                setDetectionData(prev => ({
                    ...prev,
                    isActive: false,
                    violenceAlert: null,
                    peopleCount: 0,
                    confidence: 0
                }));
                setSystemState(prev => ({ ...prev, detection: 'inactive' }));
                addNotification('info', 'Detección detenida');
            }
        } catch (err) {
            console.error('❌ Error al cambiar estado de detección:', err);
            setError(`Error: ${err.message}`);
            addNotification('error', `Error en detección: ${err.message}`);
            setSystemState(prev => ({ ...prev, detection: 'error' }));
        }
    };

    const handleQualityChange = (quality) => {
        setSettings(prev => ({ ...prev, streamQuality: quality }));
        addNotification('info', `Calidad de stream cambiada a: ${quality}`);
        console.log(`🎛️ Calidad cambiada a: ${quality}`);
    };

    // CORREGIR: Función mejorada para colores de estado
    const getStatusColor = (status) => {
        const colors = {
            active: 'bg-green-500',
            connected: 'bg-green-500',
            streaming: 'bg-green-500',
            connecting: 'bg-yellow-500',
            starting: 'bg-yellow-500',
            stopping: 'bg-yellow-500',
            buffering: 'bg-yellow-500',
            inactive: 'bg-red-500',  // CORREGIR: Rojo para inactivo
            disconnected: 'bg-red-500', // CORREGIR: Rojo para desconectado
            error: 'bg-red-500'
        };
        return colors[status] || 'bg-gray-500';
    };

    const getStatusText = (type, status) => {
        const statusTexts = {
            camera: {
                active: 'Activa',
                inactive: 'Inactiva',
                connecting: 'Conectando...',
                error: 'Error'
            },
            stream: {
                connected: 'Conectado',
                connecting: 'Conectando...',
                disconnected: 'Desconectado',
                streaming: 'Transmitiendo',
                error: 'Error'
            },
            detection: {
                active: 'Detectando',
                inactive: 'Inactiva',
                starting: 'Iniciando...',
                stopping: 'Deteniendo...',
                error: 'Error'
            },
            connection: {
                streaming: 'Streaming',
                connected: 'Conectado',
                connecting: 'Conectando...',
                buffering: 'Buffering',
                disconnected: 'Desconectado',
                error: 'Error'
            }
        };
        return statusTexts[type]?.[status] || status;
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Cargando detalles de la cámara...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-center bg-red-50 p-6 rounded-lg">
                    <div className="text-red-500 text-4xl mb-4">⚠️</div>
                    <p className="text-red-600 mb-4 font-medium">Error: {error}</p>
                    <button
                        onClick={() => setError(null)}
                        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                    >
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

    if (!cameraDetail) {
        return (
            <div className="flex justify-center items-center h-64">
                <p className="text-gray-600">Cámara no encontrada.</p>
            </div>
        );
    }

    return (
        <div className="py-6 flex justify-center">
            <div className="w-full max-w-7xl flex flex-col space-y-4">
                <button
                    onClick={() => navigate('/cameras')}
                    className="mb-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm self-start transition-colors"
                >
                    ← Volver a Cámaras
                </button>

                {/* Panel de Estado del Sistema MEJORADO */}
                <div className="bg-white rounded-lg shadow-md p-4">
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">Estado del Sistema</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { label: 'Cámara', type: 'camera', status: systemState.camera },
                            { label: 'Stream', type: 'stream', status: systemState.stream },
                            { label: 'Detección', type: 'detection', status: systemState.detection },
                            { label: 'Conexión', type: 'connection', status: systemState.connection }
                        ].map(({ label, type, status }) => (
                            <div key={type} className="flex items-center space-x-3">
                                <div className={`w-3 h-3 rounded-full ${getStatusColor(status)} ${status.includes('ing') ? 'animate-pulse' : ''}`}></div>
                                <div>
                                    <div className="text-sm font-medium text-gray-900">{label}</div>
                                    <div className="text-xs text-gray-500">{getStatusText(type, status)}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Contenedor de video mejorado */}
                <div className="relative w-full bg-gray-200 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover"
                        style={{
                            maxWidth: '100%',
                            maxHeight: '720px',
                            backgroundColor: '#000'
                        }}
                    />

                    {/* Overlay de información */}
                    <div className="absolute top-4 left-4 space-y-2">
                        <div className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(systemState.connection)} text-white`}>
                            {getStatusText('connection', systemState.connection)}
                        </div>

                        {detectionData.isActive && (
                            <div className="px-3 py-1 text-sm font-semibold rounded-full bg-purple-500 text-white animate-pulse">
                                🔍 Detectando ({detectionData.peopleCount} personas)
                            </div>
                        )}

                        {detectionData.violenceAlert && (
                            <div className="px-3 py-1 text-sm font-semibold rounded-full bg-red-500 text-white animate-pulse">
                                🚨 ALERTA DE VIOLENCIA
                            </div>
                        )}
                    </div>

                    {/* Información de la cámara MEJORADA */}
                    <div className="absolute top-4 right-4">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                            systemState.camera === "active" ? "bg-green-500 text-white" :
                            systemState.camera === "inactive" ? "bg-red-500 text-white" :
                            systemState.camera === "connecting" ? "bg-yellow-500 text-white" :
                            "bg-gray-500 text-white"
                        }`}>
                            {getStatusText('camera', systemState.camera)}
                        </span>
                    </div>

                    {/* Estadísticas en tiempo real */}
                    {systemState.stream === 'connected' && (
                        <div className="absolute bottom-4 left-4 bg-black bg-opacity-60 text-white px-3 py-2 rounded text-sm">
                            <div>FPS: {stats.frameRate}</div>
                            <div>Alertas: {stats.totalAlerts}</div>
                            {detectionData.confidence > 0 && (
                                <div>Confianza: {(detectionData.confidence * 100).toFixed(1)}%</div>
                            )}
                        </div>
                    )}
                </div>

                {/* Controles principales */}
                <div className="bg-white rounded-lg shadow-md p-4">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Controles</h2>
                    <div className="flex flex-wrap justify-center gap-4">
                        <button
                            onClick={handleToggleStream}
                            className={`px-6 py-2 rounded text-white font-medium transition-colors ${
                                systemState.stream === 'disconnected'
                                    ? "bg-green-500 hover:bg-green-600"
                                    : systemState.stream === 'connecting'
                                        ? "bg-yellow-500 cursor-not-allowed"
                                        : "bg-red-500 hover:bg-red-600"
                            }`}
                            disabled={systemState.stream === 'connecting' || detectionData.isActive}
                        >
                            {systemState.stream === 'connecting' ? "Conectando..." :
                                systemState.stream === 'disconnected' ? "Iniciar Stream" : "Detener Stream"}
                        </button>

                        <button
                            onClick={handleToggleDetection}
                            className={`px-6 py-2 rounded text-white font-medium transition-colors ${
                                detectionData.isActive
                                    ? "bg-red-500 hover:bg-red-600"
                                    : systemState.detection === 'starting'
                                        ? "bg-yellow-500 cursor-not-allowed"
                                        : "bg-blue-500 hover:bg-blue-600"
                            }`}
                            disabled={systemState.stream === 'disconnected' || systemState.detection.includes('ing')}
                        >
                            {systemState.detection === 'starting' ? "Iniciando..." :
                                systemState.detection === 'stopping' ? "Deteniendo..." :
                                    detectionData.isActive ? (
                                        <>
                                            <span className="animate-pulse">🔍</span> Detener Detección
                                        </>
                                    ) : (
                                        'Iniciar Detección'
                                    )}
                        </button>

                        {/* Control de calidad */}
                        <select
                            value={settings.streamQuality}
                            onChange={(e) => handleQualityChange(e.target.value)}
                            className="px-4 py-2 border rounded text-gray-700 bg-white"
                            disabled={systemState.stream === 'disconnected'}
                        >
                            <option value="Alta">Calidad Alta</option>
                            <option value="Media">Calidad Media</option>
                            <option value="Baja">Calidad Baja</option>
                        </select>
                    </div>
                </div>

                {/* Panel de Notificaciones */}
                {notifications.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-4">
                        <h2 className="text-lg font-semibold text-gray-900 mb-3">Notificaciones</h2>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {notifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className={`p-3 rounded-lg border-l-4 ${
                                        notification.type === 'violence' ? 'bg-red-50 border-red-500' :
                                        notification.type === 'error' ? 'bg-red-50 border-red-400' :
                                        notification.type === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                                        'bg-blue-50 border-blue-400'
                                    }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <p className={`font-medium ${
                                                notification.type === 'violence' ? 'text-red-800' :
                                                notification.type === 'error' ? 'text-red-700' :
                                                notification.type === 'warning' ? 'text-yellow-700' :
                                                'text-blue-700'
                                            }`}>
                                                {notification.message}
                                            </p>
                                            <p className="text-sm text-gray-500 mt-1">
                                                {notification.timestamp.toLocaleTimeString()}
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => setNotifications(prev =>
                                                prev.filter(n => n.id !== notification.id)
                                            )}
                                            className="text-gray-400 hover:text-gray-600 ml-2"
                                        >
                                            ×
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Alertas de detección detalladas CORREGIDAS */}
                {detectionData.violenceAlert && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 animate-pulse">
                        <h2 className="text-xl font-semibold text-red-800 mb-2">🚨 Alerta de Violencia Crítica</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-red-700">
                            <div>
                                <p className="font-medium">Probabilidad:</p>
                                <p className="text-2xl font-bold">
                                    {((detectionData.violenceAlert.probability || 0) * 100).toFixed(1)}%
                                </p>
                            </div>
                            <div>
                                <p className="font-medium">Personas detectadas:</p>
                                <p className="text-2xl font-bold">
                                    {detectionData.violenceAlert.peopleCount || 0}
                                </p>
                            </div>
                            <div>
                                <p className="font-medium">Ubicación:</p>
                                <p className="font-bold">{detectionData.violenceAlert.location}</p>
                                <p className="text-sm text-red-600">
                                    {detectionData.violenceAlert.timestamp.toLocaleString()}
                                </p>
                            </div>
                        </div>
                        <div className="mt-4 flex space-x-4">
                            <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors">
                                Ver Evidencia
                            </button>
                            <button className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors">
                                Notificar Autoridades
                            </button>
                            <button
                                onClick={() => setDetectionData(prev => ({ ...prev, violenceAlert: null }))}
                                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                            >
                                Descartar Alerta
                            </button>
                        </div>
                    </div>
                )}

                {/* Detalles de la cámara */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Información de la Cámara</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-base">
                        {[
                            { label: "ID", value: cameraDetail.id },
                            { label: "Nombre", value: cameraDetail.nombre },
                            { label: "Ubicación", value: cameraDetail.ubicacion },
                            { label: "Descripción", value: cameraDetail.descripcion || "N/A" },
                            { label: "Tipo de Cámara", value: cameraDetail.tipo_camara.toUpperCase() },
                            { label: "Resolución", value: `${cameraDetail.resolucion_ancho}x${cameraDetail.resolucion_alto}` },
                            { label: "FPS", value: cameraDetail.fps },
                            { label: "Fecha de Instalación", value: new Date(cameraDetail.fecha_instalacion).toLocaleString() },
                            { label: "Última Actividad", value: new Date(cameraDetail.ultima_actividad).toLocaleString() }
                        ].map(({ label, value }, index) => (
                            <p key={index} className="text-gray-700">
                                <span className="font-bold">{label}:</span>
                                <span className="font-normal ml-2">{value}</span>
                            </p>
                        ))}
                    </div>
                </div>

                {/* Panel de configuración */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuración</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="flex items-center space-x-3">
                                <input
                                    type="checkbox"
                                    checked={settings.autoRecord}
                                    onChange={(e) => setSettings(prev => ({ ...prev, autoRecord: e.target.checked }))}
                                    className="form-checkbox h-5 w-5 text-blue-600"
                                />
                                <span className="text-gray-700">Grabación automática de evidencia</span>
                            </label>
                        </div>
                        <div>
                            <label className="flex items-center space-x-3">
                                <input
                                    type="checkbox"
                                    checked={settings.soundAlerts}
                                    onChange={(e) => setSettings(prev => ({ ...prev, soundAlerts: e.target.checked }))}
                                    className="form-checkbox h-5 w-5 text-blue-600"
                                />
                                <span className="text-gray-700">Alertas sonoras</span>
                            </label>
                        </div>
                        <div>
                            <label className="block text-gray-700 mb-2">Sensibilidad de detección:</label>
                            <select
                                value={settings.sensitivity}
                                onChange={(e) => setSettings(prev => ({ ...prev, sensitivity: e.target.value }))}
                                className="w-full px-3 py-2 border rounded text-gray-700"
                            >
                                <option value="Baja">Baja</option>
                                <option value="Media">Media</option>
                                <option value="Alta">Alta</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Información de rendimiento (solo visible en desarrollo) */}
                {process.env.NODE_ENV === 'development' && (
                    <div className="bg-gray-50 rounded-lg p-4 text-sm">
                        <h3 className="font-semibold text-gray-800 mb-2">Debug Info</h3>
                        <div className="grid grid-cols-2 gap-2 text-gray-600">
                            <span>Estado Stream: {systemState.stream}</span>
                            <span>Estado Detección: {systemState.detection}</span>
                            <span>Conexión: {systemState.connection}</span>
                            <span>Calidad: {settings.streamQuality}</span>
                            <span>Personas: {detectionData.peopleCount}</span>
                            <span>Confianza: {(detectionData.confidence * 100).toFixed(1)}%</span>
                            {videoRef.current && (
                                <>
                                    <span>Video Width: {videoRef.current.videoWidth || 'N/A'}</span>
                                    <span>Video Height: {videoRef.current.videoHeight || 'N/A'}</span>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CameraDetail;