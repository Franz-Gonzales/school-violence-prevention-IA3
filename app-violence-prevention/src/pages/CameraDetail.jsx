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

    // *** IMPORTANTE: Definir handleDetectionEnd PRIMERO ***
    const handleDetectionEnd = useCallback((data) => {
        console.log('🧹 Finalizando detección de violencia:', data);

        // Limpiar estado de violencia
        setDetectionData(prev => ({
            ...prev,
            violenceAlert: null,
            peopleCount: 0,
            confidence: 0
        }));

        // Remover efectos visuales de alerta del video
        if (videoRef.current) {
            videoRef.current.style.border = 'none';
            videoRef.current.style.boxShadow = 'none';
        }

        // Notificación de finalización
        addNotification(
            'info',
            '✅ Alerta de violencia finalizada - Área segura',
            {
                timestamp: new Date(),
                location: data.ubicacion || data.location
            }
        );

        console.log('✅ Estado de alerta limpiado correctamente');
    }, [addNotification]);

    // *** AHORA DEFINIR handleDetection (que usa handleDetectionEnd) ***
    const handleDetection = useCallback((data) => {
        console.log('🔍 Datos de detección recibidos RAW:', data);

        // *** NUEVO: Manejar fin de detección de violencia ***
        if (data.tipo === 'deteccion_violencia_fin' || data.limpiar_alerta) {
            handleDetectionEnd(data);
            return;
        }

        // *** VERIFICAR TODOS LOS CAMPOS POSIBLES DE PROBABILIDAD ***
        let probabilidadReal = 0;

        // Intentar obtener probabilidad de múltiples campos
        if (data.probabilidad !== undefined && data.probabilidad !== null) {
            probabilidadReal = data.probabilidad;
        } else if (data.probability !== undefined && data.probability !== null) {
            probabilidadReal = data.probability;
        } else if (data.probabilidad_violencia !== undefined && data.probabilidad_violencia !== null) {
            probabilidadReal = data.probabilidad_violencia;
        }

        // *** VERIFICAR Y EXTRAER OTROS DATOS ***
        const personasDetectadas = data.personas_detectadas || data.peopleCount || 0;
        const ubicacionReal = data.ubicacion || data.location || cameraDetail?.ubicacion || 'Ubicación no disponible';

        console.log('📊 Datos procesados para notificación:', {
            probabilidad_raw: data.probabilidad,
            probability_raw: data.probability,
            probabilidad_violencia_raw: data.probabilidad_violencia,
            probabilidad_final: probabilidadReal,
            personas: personasDetectadas,
            ubicacion: ubicacionReal
        });

        setDetectionData(prev => ({
            ...prev,
            lastDetection: new Date(),
            peopleCount: personasDetectadas,
            confidence: probabilidadReal
        }));

        if (data.violencia_detectada) {
            const alertData = {
                probabilidad: probabilidadReal,
                probability: probabilidadReal,
                probabilidad_violencia: probabilidadReal,
                personas_detectadas: personasDetectadas,
                peopleCount: personasDetectadas,
                ubicacion: ubicacionReal,
                location: ubicacionReal,
                timestamp: new Date(),
                cameraId: cameraId
            };

            setDetectionData(prev => ({
                ...prev,
                violenceAlert: alertData
            }));

            // *** NOTIFICACIÓN CON DATOS REALES ***
            const probabilidadPorcentaje = (probabilidadReal * 100).toFixed(1);

            console.log('🚨 Creando notificación con:', {
                mensaje: `VIOLENCIA DETECTADA - Probabilidad: ${probabilidadPorcentaje}%`,
                alertData: alertData,
                probabilidad_verificada: probabilidadReal
            });

            addNotification(
                'violence',
                `🚨 VIOLENCIA DETECTADA - Probabilidad: ${probabilidadPorcentaje}%`,
                alertData
            );

            console.log('✅ Notificación creada exitosamente');

            // Efecto visual de alerta
            if (videoRef.current) {
                videoRef.current.style.border = '4px solid #ff0000';
                videoRef.current.style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.7)';

                // NUEVO: Auto-remover el efecto visual después de 8 segundos
                setTimeout(() => {
                    if (videoRef.current) {
                        videoRef.current.style.border = 'none';
                        videoRef.current.style.boxShadow = 'none';
                    }
                }, 8000);
            }

            setStats(prev => ({ ...prev, totalAlerts: prev.totalAlerts + 1 }));
        }
    }, [cameraId, cameraDetail?.ubicacion, addNotification, handleDetectionEnd]);

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

    const getLocationIcon = (ubicacion) => {
        if (!ubicacion) { return '🏫'; }
        const location = ubicacion.toLowerCase();
        if (location.includes('patio') || location.includes('recreo')) { return '🏃‍♂️'; }
        if (location.includes('aula') || location.includes('salon')) { return '📚'; }
        if (location.includes('pasillo') || location.includes('corredor')) { return '🚶‍♂️'; }
        if (location.includes('entrada') || location.includes('acceso')) { return '🚪'; }
        if (location.includes('biblioteca')) { return '📖'; }
        if (location.includes('laboratorio')) { return '🔬'; }
        if (location.includes('gimnasio') || location.includes('deportes')) { return '🏃‍♀️'; }
        if (location.includes('cafeteria') || location.includes('comedor')) { return '🍽️'; }
        { return '🏫'; }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
                <div className="flex justify-center items-center h-screen">
                    <div className="text-center">
                        <div className="relative mb-8">
                            <div className="animate-spin rounded-full h-20 w-20 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-8 h-8 bg-blue-600 rounded-full animate-pulse"></div>
                            </div>
                        </div>
                        <h2 className="text-2xl font-semibold text-gray-800 mb-2">Cargando Sistema de Cámara</h2>
                        <p className="text-gray-600">Obteniendo detalles de la cámara educativa...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-pink-50">
                <div className="flex justify-center items-center h-screen">
                    <div className="text-center max-w-md mx-auto p-8 bg-white rounded-2xl shadow-xl border border-red-200">
                        <div className="text-red-600 text-6xl mb-6 animate-bounce">⚠️</div>
                        <h1 className="text-2xl font-bold text-gray-900 mb-4">Error en el Sistema</h1>
                        <p className="text-red-600 mb-6 font-medium">{error}</p>
                        <button
                            onClick={() => navigate('/cameras')}
                            className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all transform hover:scale-105 shadow-lg"
                        >
                            🔙 Volver a Cámaras
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!cameraDetail) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50">
                <div className="flex justify-center items-center h-screen">
                    <div className="text-center p-8 bg-white rounded-2xl shadow-xl">
                        <div className="text-gray-500 text-6xl mb-4">📹</div>
                        <p className="text-gray-600 text-xl">Cámara no encontrada en el sistema educativo.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
            <div className="p-6">

                {/* Header educativo mejorado */}
                <div className="bg-white rounded-2xl shadow-xl border border-blue-100 p-6 mb-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full -translate-y-16 translate-x-16 opacity-50"></div>

                    <div className="relative z-10 flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => navigate('/cameras')}
                                className="group flex items-center text-gray-600 hover:text-gray-900 transition-all transform hover:scale-105"
                            >
                                <div className="p-3 rounded-xl bg-gradient-to-r from-gray-100 to-gray-200 group-hover:from-blue-100 group-hover:to-indigo-100 transition-all mr-3 shadow-md">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                </div>
                                <span className="font-semibold">Volver al Sistema</span>
                            </button>

                            <div className="flex items-center space-x-4">
                                <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg">
                                    <span className="text-2xl">{getLocationIcon(cameraDetail.ubicacion)}</span>
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-800 to-indigo-800 bg-clip-text text-transparent">
                                        {cameraDetail.nombre}
                                    </h1>
                                    <div className="flex items-center space-x-4 mt-1">
                                        <p className="text-gray-600 flex items-center">
                                            <span className="mr-1">📍</span>
                                            {cameraDetail.ubicacion}
                                        </p>
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm text-gray-500">ID:</span>
                                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-bold">
                                                CAM-{String(cameraDetail.id).padStart(3, '0')}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="text-right">
                            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-4 border border-green-200">
                                <div className="text-sm text-gray-600 mb-1">Estado del Sistema</div>
                                <div className={`text-lg font-bold ${systemState.camera === 'active' ? 'text-green-600' :
                                        systemState.camera === 'inactive' ? 'text-red-600' : 'text-yellow-600'
                                    }`}>
                                    {getStatusText('camera', systemState.camera)}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Panel de Estado del Sistema - Horizontal */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 mb-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3">
                            <div className="p-3 bg-gradient-to-br from-green-500 to-blue-500 rounded-xl">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-gray-900">Monitor de Estado Educativo</h2>
                                <p className="text-gray-600">Supervisión en tiempo real del área de {cameraDetail.ubicacion}</p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-4 gap-6">
                        {[
                            { label: 'Cámara', type: 'camera', status: systemState.camera, icon: '📹' },
                            { label: 'Transmisión', type: 'stream', status: systemState.stream, icon: '📡' },
                            { label: 'Detección IA', type: 'detection', status: systemState.detection, icon: '🤖' },
                            { label: 'Conexión', type: 'connection', status: systemState.connection, icon: '🔗' }
                        ].map(({ label, type, status, icon }) => (
                            <div key={type} className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                                <div className="flex items-center space-x-3 mb-2">
                                    <span className="text-2xl">{icon}</span>
                                    <div className={`w-3 h-3 rounded-full ${getStatusColor(status)} ${status.includes('ing') ? 'animate-pulse' : ''}`}></div>
                                </div>
                                <div className="text-sm font-semibold text-gray-800">{label}</div>
                                <div className="text-xs text-blue-700 font-medium">{getStatusText(type, status)}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Contenedor de video principal - CORREGIDO: VOLVER A 16:9 */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden mb-6">

                    {/* Header del video */}
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-white/20 rounded-lg">
                                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Monitoreo en Vivo</h3>
                                    <p className="text-blue-100 text-sm">Área: {cameraDetail.ubicacion}</p>
                                </div>
                            </div>

                            <div className="flex items-center space-x-2">
                                {systemState.stream === 'connected' && (
                                    <div className="bg-red-500 px-3 py-1 rounded-full text-white text-xs font-bold flex items-center space-x-1 animate-pulse">
                                        <div className="w-2 h-2 bg-white rounded-full"></div>
                                        <span>EN VIVO</span>
                                    </div>
                                )}
                                <div className={`px-3 py-1 rounded-full text-xs font-bold text-white ${systemState.connection === 'streaming' ? 'bg-green-500' :
                                        systemState.connection === 'connecting' ? 'bg-yellow-500' :
                                            'bg-gray-500'
                                    }`}>
                                    {getStatusText('connection', systemState.connection)}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Área de video - CORREGIDO: VOLVER A 16:9 COMO EL ORIGINAL */}
                    <div className="relative bg-gradient-to-br from-gray-800 to-gray-900" style={{ aspectRatio: '16/9' }}>
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover bg-black"
                            style={{
                                maxWidth: '100%',
                                maxHeight: '720px',
                                backgroundColor: '#000'
                            }}
                        />

                        {/* Overlays informativos */}
                        <div className="absolute top-4 left-4 space-y-2">
                            {detectionData.isActive && (
                                <div className="px-3 py-1 text-sm font-bold rounded-full bg-purple-500 text-white animate-pulse flex items-center space-x-2">
                                    <span>🤖</span>
                                    <span>IA Detectando ({detectionData.peopleCount} personas)</span>
                                </div>
                            )}

                            {detectionData.violenceAlert && (
                                <div className="px-3 py-1 text-sm font-bold rounded-full bg-red-500 text-white animate-pulse flex items-center space-x-2">
                                    <span>🚨</span>
                                    <span>ALERTA DE SEGURIDAD</span>
                                </div>
                            )}
                        </div>

                        {/* Estadísticas en tiempo real */}
                        {systemState.stream === 'connected' && (
                            <div className="absolute bottom-4 left-4 bg-black/70 text-white px-4 py-2 rounded-lg text-sm backdrop-blur-sm">
                                <div className="flex items-center space-x-6">
                                    <span>📊 FPS: {stats.frameRate}</span>
                                    <span>🚨 Alertas: {stats.totalAlerts}</span>
                                    {detectionData.confidence > 0 && (
                                        <span>🎯 Confianza: {(detectionData.confidence * 100).toFixed(1)}%</span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Mensaje cuando no hay video */}
                        {systemState.stream === 'disconnected' && (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center text-white">
                                    <div className="text-8xl mb-6 opacity-50">📹</div>
                                    <h3 className="text-2xl font-bold mb-3">Cámara sin conexión</h3>
                                    <p className="text-gray-300 text-lg">Haga clic en "Iniciar Stream" para comenzar el monitoreo</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Controles principales mejorados */}
                    <div className="p-6 bg-gradient-to-r from-gray-50 to-blue-50 border-t border-gray-200">
                        <div className="flex flex-wrap justify-center gap-4">
                            <button
                                onClick={handleToggleStream}
                                className={`px-8 py-3 rounded-xl text-white font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-3 ${systemState.stream === 'disconnected'
                                        ? "bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                                        : systemState.stream === 'connecting'
                                            ? "bg-gradient-to-r from-yellow-500 to-orange-500 cursor-not-allowed"
                                            : "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700"
                                    }`}
                                disabled={systemState.stream === 'connecting' || detectionData.isActive}
                            >
                                <span className="text-xl">
                                    {systemState.stream === 'connecting' ? "⏳" :
                                        systemState.stream === 'disconnected' ? "▶️" : "⏹️"}
                                </span>
                                <span>
                                    {systemState.stream === 'connecting' ? "Conectando..." :
                                        systemState.stream === 'disconnected' ? "Iniciar Stream" : "Detener Stream"}
                                </span>
                            </button>

                            <button
                                onClick={handleToggleDetection}
                                className={`px-8 py-3 rounded-xl text-white font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center space-x-3 ${detectionData.isActive
                                        ? "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700"
                                        : systemState.detection === 'starting'
                                            ? "bg-gradient-to-r from-yellow-500 to-orange-500 cursor-not-allowed"
                                            : "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                                    }`}
                                disabled={systemState.stream === 'disconnected' || systemState.detection.includes('ing')}
                            >
                                <span className="text-xl">
                                    {systemState.detection === 'starting' ? "🔄" :
                                        systemState.detection === 'stopping' ? "⏳" :
                                            detectionData.isActive ? "🤖" : "🔍"}
                                </span>
                                <span>
                                    {systemState.detection === 'starting' ? "Iniciando..." :
                                        systemState.detection === 'stopping' ? "Deteniendo..." :
                                            detectionData.isActive ? "Detener IA" : 'Activar IA'}
                                </span>
                            </button>

                            {/* Control de calidad */}
                            <select
                                value={settings.streamQuality}
                                onChange={(e) => handleQualityChange(e.target.value)}
                                className="px-6 py-3 border-2 border-blue-200 rounded-xl text-gray-700 bg-white hover:border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold"
                                disabled={systemState.stream === 'disconnected'}
                            >
                                <option value="Alta">🔥 Calidad Alta</option>
                                <option value="Media">⚡ Calidad Media</option>
                                <option value="Baja">💡 Calidad Baja</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Alerta de violencia crítica mejorada - ANCHO COMPLETO */}
                {detectionData.violenceAlert && (
                    <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-2xl p-6 animate-pulse shadow-xl mb-6">
                        <div className="flex items-center space-x-4 mb-4">
                            <div className="p-3 bg-red-500 rounded-full animate-bounce">
                                <span className="text-2xl text-white">🚨</span>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-red-800">¡ALERTA DE SEGURIDAD CRÍTICA!</h2>
                                <p className="text-red-700 font-medium">Situación detectada en {cameraDetail.ubicacion}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-white rounded-xl p-4 border-2 border-red-200">
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-red-600 mb-1">
                                        {(() => {
                                            let prob = 0;
                                            const alert = detectionData.violenceAlert;
                                            if (alert.probabilidad !== undefined && alert.probabilidad !== null) {
                                                prob = alert.probabilidad;
                                            } else if (alert.probability !== undefined && alert.probability !== null) {
                                                prob = alert.probability;
                                            } else if (alert.probabilidad_violencia !== undefined && alert.probabilidad_violencia !== null) {
                                                prob = alert.probabilidad_violencia;
                                            }
                                            return `${(prob * 100).toFixed(1)}%`;
                                        })()}
                                    </div>
                                    <div className="text-sm font-semibold text-red-800">Probabilidad</div>
                                </div>
                            </div>

                            <div className="bg-white rounded-xl p-4 border-2 border-orange-200">
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-orange-600 mb-1">
                                        {detectionData.violenceAlert.personas_detectadas || detectionData.violenceAlert.peopleCount || 0}
                                    </div>
                                    <div className="text-sm font-semibold text-orange-800">Personas</div>
                                </div>
                            </div>

                            <div className="bg-white rounded-xl p-4 border-2 border-blue-200">
                                <div className="text-center">
                                    <div className="text-lg font-bold text-blue-600 mb-1">
                                        {detectionData.violenceAlert.timestamp.toLocaleTimeString()}
                                    </div>
                                    <div className="text-sm font-semibold text-blue-800">Hora de Detección</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Información detallada - DEBAJO DEL VIDEO, NO EN CARDS */}
                <div className="space-y-6">

                    {/* Información técnica - Layout horizontal limpio */}
                    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
                        <div className="flex items-center space-x-4 mb-6">
                            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-gray-900">Información Técnica de la Cámara</h3>
                                <p className="text-gray-600">Especificaciones y detalles técnicos del dispositivo de monitoreo</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                            {[
                                { label: 'Ubicación', value: cameraDetail.ubicacion, icon: '📍', color: 'text-blue-600' },
                                { label: 'Tipo', value: cameraDetail.tipo_camara.toUpperCase(), icon: '📹', color: 'text-green-600' },
                                { label: 'Resolución', value: `${cameraDetail.resolucion_ancho}x${cameraDetail.resolucion_alto}`, icon: '🖥️', color: 'text-purple-600' },
                                { label: 'FPS', value: cameraDetail.fps, icon: '⚡', color: 'text-orange-600' },
                                { label: 'Instalación', value: new Date(cameraDetail.fecha_instalacion).toLocaleDateString('es-ES'), icon: '📅', color: 'text-indigo-600' }
                            ].map((item, index) => (
                                <div key={index} className="text-center">
                                    <div className="flex items-center justify-center mb-3">
                                        <span className="text-3xl mr-2">{item.icon}</span>
                                        <div className={`w-3 h-3 rounded-full ${item.color.replace('text-', 'bg-')}`}></div>
                                    </div>
                                    <div className="text-sm font-medium text-gray-600 mb-1">{item.label}</div>
                                    <div className={`text-lg font-bold ${item.color}`}>{item.value}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Configuraciones y controles - Layout horizontal */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                        {/* Configuración de seguridad */}
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Configuración de Seguridad</h3>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <div className="flex items-center space-x-3">
                                        <span className="text-green-600 text-xl">🎥</span>
                                        <span className="text-sm font-medium text-gray-700">Grabación automática de evidencia</span>
                                    </div>
                                    <input
                                        type="checkbox"
                                        checked={settings.autoRecord}
                                        onChange={(e) => setSettings(prev => ({ ...prev, autoRecord: e.target.checked }))}
                                        className="form-checkbox h-5 w-5 text-green-600 rounded focus:ring-green-500"
                                    />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                    <div className="flex items-center space-x-3">
                                        <span className="text-blue-600 text-xl">🔊</span>
                                        <span className="text-sm font-medium text-gray-700">Alertas sonoras</span>
                                    </div>
                                    <input
                                        type="checkbox"
                                        checked={settings.soundAlerts}
                                        onChange={(e) => setSettings(prev => ({ ...prev, soundAlerts: e.target.checked }))}
                                        className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
                                    />
                                </div>

                                <div className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                    <div className="flex items-center space-x-3 mb-2">
                                        <span className="text-purple-600 text-xl">🎯</span>
                                        <span className="text-sm font-medium text-gray-700">Sensibilidad de detección IA:</span>
                                    </div>
                                    <select
                                        value={settings.sensitivity}
                                        onChange={(e) => setSettings(prev => ({ ...prev, sensitivity: e.target.value }))}
                                        className="w-full px-3 py-2 border-2 border-purple-200 rounded-lg text-gray-700 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                                    >
                                        <option value="Baja">🟢 Baja (Conservador)</option>
                                        <option value="Media">🟡 Media (Balanceado)</option>
                                        <option value="Alta">🔴 Alta (Sensible)</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Estadísticas de rendimiento */}
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Rendimiento del Sistema</h3>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                        <div className="text-2xl font-bold text-green-600">{stats.frameRate}</div>
                                        <div className="text-xs text-green-700 font-semibold">FPS</div>
                                    </div>
                                    <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                                        <div className="text-2xl font-bold text-blue-600">{stats.totalAlerts}</div>
                                        <div className="text-xs text-blue-700 font-semibold">Alertas</div>
                                    </div>
                                </div>

                                {detectionData.confidence > 0 && (
                                    <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                        <div className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                            <span className="mr-2">🎯</span>
                                            Nivel de Confianza IA
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-4">
                                            <div
                                                className="bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full transition-all duration-300"
                                                style={{ width: `${(detectionData.confidence * 100)}%` }}
                                            ></div>
                                        </div>
                                        <div className="text-sm text-purple-700 mt-2 font-bold text-center">
                                            {(detectionData.confidence * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                )}

                                <div className="p-4 bg-gradient-to-r from-gray-50 to-slate-50 rounded-lg border border-gray-200">
                                    <div className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                        <span className="mr-2">⚡</span>
                                        Estado General
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3">
                                        <div className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full w-[95%] animate-pulse"></div>
                                    </div>
                                    <div className="text-sm text-green-600 mt-2 font-bold text-center">95% Óptimo</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Panel de notificaciones - Solo si hay notificaciones */}
                    {notifications.length > 0 && (
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="p-2 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM19 12H5l7-7 7 7z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Registro de Eventos Recientes</h3>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                {notifications.slice(0, 6).map((notification) => (
                                    <div
                                        key={notification.id}
                                        className={`p-3 rounded-lg border-l-4 transition-all hover:shadow-md ${notification.type === 'violence' ? 'bg-red-50 border-red-500' :
                                                notification.type === 'error' ? 'bg-red-50 border-red-400' :
                                                    notification.type === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                                                        'bg-blue-50 border-blue-400'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-lg">
                                                        {notification.type === 'violence' ? '🚨' :
                                                            notification.type === 'error' ? '❌' :
                                                                notification.type === 'warning' ? '⚠️' : 'ℹ️'}
                                                    </span>
                                                    <span className={`text-sm font-semibold ${notification.type === 'violence' ? 'text-red-800' :
                                                            notification.type === 'error' ? 'text-red-700' :
                                                                notification.type === 'warning' ? 'text-yellow-700' :
                                                                    'text-blue-700'
                                                        }`}>
                                                        {notification.message}
                                                    </span>
                                                </div>
                                                <div className="text-xs text-gray-500 font-medium">
                                                    {notification.timestamp.toLocaleTimeString()}
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => setNotifications(prev =>
                                                    prev.filter(n => n.id !== notification.id)
                                                )}
                                                className="text-gray-400 hover:text-gray-600 ml-2 p-1 rounded-full hover:bg-gray-200 transition-all"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Información educativa final */}
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl shadow-lg border border-blue-200 p-8">
                        <div className="text-center">
                            <div className="text-6xl mb-4">🏫</div>
                            <h3 className="text-2xl font-bold text-blue-800 mb-3">Centro Educativo Protegido</h3>
                            <p className="text-blue-700 mb-6 text-lg">
                                Sistema de inteligencia artificial monitoreando continuamente para garantizar un ambiente de aprendizaje seguro.
                            </p>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-white/70 rounded-lg p-4">
                                    <div className="font-bold text-green-600 text-lg">✅ Detección IA</div>
                                    <div className="text-gray-600">Tiempo Real</div>
                                </div>
                                <div className="bg-white/70 rounded-lg p-4">
                                    <div className="font-bold text-blue-600 text-lg">🛡️ Protección</div>
                                    <div className="text-gray-600">24/7</div>
                                </div>
                                <div className="bg-white/70 rounded-lg p-4">
                                    <div className="font-bold text-purple-600 text-lg">📊 Análisis</div>
                                    <div className="text-gray-600">Avanzado</div>
                                </div>
                                <div className="bg-white/70 rounded-lg p-4">
                                    <div className="font-bold text-orange-600 text-lg">🎯 Precisión</div>
                                    <div className="text-gray-600">Alta</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CameraDetail;