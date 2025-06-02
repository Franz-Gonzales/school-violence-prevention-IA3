import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCameras, api } from '../utils/api';
import WebRTCClient from '../utils/webrtc';

const CameraDetail = () => {
    const { cameraId } = useParams();
    const navigate = useNavigate();
    const videoRef = useRef(null);
    const webRTCClientRef = useRef(null);

    const [cameraDetail, setCameraDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isStreamActive, setIsStreamActive] = useState(false);
    const [isDetectionActive, setIsDetectionActive] = useState(false);
    const [deteccion, setDeteccion] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('Desconectado');
    const [streamQuality, setStreamQuality] = useState('Alta');

    // Cleanup function
    const cleanup = useCallback(() => {
        if (webRTCClientRef.current) {
            console.log('Limpiando recursos WebRTC...');
            webRTCClientRef.current.stop();
            webRTCClientRef.current = null;
        }
        setIsStreamActive(false);
        setIsDetectionActive(false);
        setDeteccion(null);
        setConnectionStatus('Desconectado');
    }, []);

    useEffect(() => {
        const fetchCamera = async () => {
            try {
                const cameras = await getCameras();
                const camera = cameras.find(cam => cam.id === Number(cameraId));
                if (!camera) { 
                    throw new Error('Cámara no encontrada'); 
                }
                setCameraDetail(camera);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };
        
        fetchCamera();

        // Cleanup al desmontar el componente
        return cleanup;
    }, [cameraId, cleanup]);

    // Configurar video element para mejor rendimiento
    useEffect(() => {
        if (videoRef.current) {
            const video = videoRef.current;
            
            // Configurar propiedades del video
            video.playsInline = true;
            video.muted = true;
            video.autoplay = true;
            video.controls = false;
            
            // Configurar eventos del video
            video.addEventListener('loadstart', () => {
                console.log('Video cargando...');
            });
            
            video.addEventListener('loadedmetadata', () => {
                console.log('Metadatos del video cargados');
                console.log(`Resolución: ${video.videoWidth}x${video.videoHeight}`);
            });
            
            video.addEventListener('canplay', () => {
                console.log('Video listo para reproducir');
                setConnectionStatus('Conectado');
            });
            
            video.addEventListener('stalled', () => {
                console.log('Video pausado - buffering');
                setConnectionStatus('Buffering');
            });
            
            video.addEventListener('waiting', () => {
                console.log('Video esperando datos');
                setConnectionStatus('Buffering');
            });
            
            video.addEventListener('playing', () => {
                console.log('Video reproduciéndose');
                setConnectionStatus('Streaming');
            });
            
            video.addEventListener('error', (e) => {
                console.error('Error en video:', e);
                setConnectionStatus('Error');
            });
        }
    }, []);

    const handleDetection = useCallback((data) => {
        console.log('Datos de detección recibidos:', data);
        setDeteccion(data);

        // Solo actualizar el estado si hay una detección de violencia
        if (data.violencia_detectada) {
            console.log('¡ALERTA! Violencia detectada:', data.probabilidad);
            
            // Opcional: hacer que el video parpadee para alertar
            if (videoRef.current) {
                videoRef.current.style.border = '3px solid red';
                setTimeout(() => {
                    if (videoRef.current) {
                        videoRef.current.style.border = 'none';
                    }
                }, 2000);
            }
        }
    }, []);

    const handleToggleStream = async () => {
        try {
            if (!isStreamActive) {
                console.log('Iniciando stream...');
                setConnectionStatus('Conectando...');
                
                // Activar cámara en el backend
                await api.post(`/api/v1/cameras/${cameraId}/activar`);
                
                // Crear nuevo cliente WebRTC
                const client = new WebRTCClient(cameraId, videoRef.current, handleDetection);
                webRTCClientRef.current = client;
                
                // Conectar sin detección inicialmente
                await client.connect(false);
                setIsStreamActive(true);
                console.log('Stream iniciado exitosamente');
                
            } else {
                console.log('Deteniendo stream...');
                setConnectionStatus('Desconectando...');
                
                // Desactivar cámara en el backend
                await api.post(`/api/v1/cameras/${cameraId}/desactivar`);
                
                // Limpiar cliente WebRTC
                cleanup();
                console.log('Stream detenido');
            }
        } catch (err) {
            console.error('Error al manejar stream:', err);
            setError(`Error al manejar stream: ${err.message}`);
            setConnectionStatus('Error');
            // En caso de error, limpiar todo
            cleanup();
        }
    };

    const handleToggleDetection = async () => {
        if (!webRTCClientRef.current) {
            setError('Debe iniciar el stream primero.');
            return;
        }

        try {
            if (!isDetectionActive) {
                console.log('Activando detección...');
                
                // Activar cámara en el backend (por si acaso)
                await api.post(`/api/v1/cameras/${cameraId}/activar`);
                
                // Activar detección en el cliente WebRTC
                webRTCClientRef.current.toggleDetection(true);
                setIsDetectionActive(true);
                console.log('Detección activada');
                
            } else {
                console.log('Desactivando detección...');
                
                // Desactivar detección en el cliente WebRTC
                webRTCClientRef.current.toggleDetection(false);
                setIsDetectionActive(false);
                setDeteccion(null);
                console.log('Detección desactivada');
            }
        } catch (err) {
            console.error('Error al cambiar estado de detección:', err);
            setError(`Error: ${err.message}`);
        }
    };

    const handleQualityChange = (quality) => {
        setStreamQuality(quality);
        // Aquí podrías enviar la configuración de calidad al backend si fuera necesario
        console.log(`Calidad cambiada a: ${quality}`);
    };

    if (loading) { 
        return (
            <div className="flex justify-center items-center h-64">
                <p className="text-gray-600">Cargando detalles de la cámara...</p>
            </div>
        ); 
    }
    
    if (error) { 
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-center">
                    <p className="text-red-600 mb-4">Error: {error}</p>
                    <button 
                        onClick={() => setError(null)}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
            <div className="w-full max-w-6xl flex flex-col space-y-2">
                <button
                    onClick={() => navigate('/cameras')}
                    className="mb-6 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm self-start"
                >
                    ← Volver a Cámaras
                </button>

                {/* Contenedor de video mejorado */}
                <div className="relative w-full bg-gray-200 rounded-lg overflow-hidden" style={{ aspectRatio: '4.7/3' }}>
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
                    
                    {/* Overlay de estado */}
                    <div className="absolute top-4 left-4 flex flex-col space-y-2">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                            connectionStatus === 'Streaming' ? 'bg-green-500 text-white' :
                            connectionStatus === 'Conectado' ? 'bg-blue-500 text-white' :
                            connectionStatus === 'Buffering' ? 'bg-yellow-500 text-white' :
                            connectionStatus === 'Error' ? 'bg-red-500 text-white' :
                            'bg-gray-500 text-white'
                        }`}>
                            {connectionStatus}
                        </span>
                        
                        {isDetectionActive && (
                            <span className="px-3 py-1 text-sm font-semibold rounded-full bg-purple-500 text-white animate-pulse">
                                ● Detección Activa
                            </span>
                        )}
                    </div>

                    {/* Estado de cámara */}
                    <span className={`absolute top-4 right-4 px-3 py-1 text-sm font-semibold rounded-full ${
                        cameraDetail.estado === "activa" ? "bg-green-500 text-white" :
                        cameraDetail.estado === "inactiva" ? "bg-red-500 text-white" :
                        cameraDetail.estado === "mantenimiento" ? "bg-yellow-500 text-white" :
                        "bg-gray-500 text-white"
                    }`}>
                        {cameraDetail.estado.charAt(0).toUpperCase() + cameraDetail.estado.slice(1)}
                    </span>
                </div>

                {/* Controles principales */}
                <div className="bg-white rounded-lg shadow-md p-4">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Controles</h2>
                    <div className="flex flex-wrap justify-center gap-4">
                        <button
                            onClick={handleToggleStream}
                            className={`px-6 py-2 rounded text-white font-medium ${
                                isStreamActive 
                                    ? "bg-red-500 hover:bg-red-600" 
                                    : "bg-green-500 hover:bg-green-600"
                            }`}
                            disabled={isDetectionActive}
                        >
                            {isStreamActive ? "Detener Stream" : "Iniciar Stream"}
                        </button>
                        
                        <button
                            onClick={handleToggleDetection}
                            className={`px-6 py-2 rounded text-white font-medium ${
                                isDetectionActive
                                    ? "bg-red-500 hover:bg-red-600"
                                    : "bg-blue-500 hover:bg-blue-600"
                            }`}
                            disabled={!isStreamActive}
                        >
                            {isDetectionActive ? (
                                <>
                                    <span className="animate-pulse">●</span> Detener Detección
                                </>
                            ) : (
                                'Iniciar Detección'
                            )}
                        </button>

                        {/* Control de calidad */}
                        <select
                            value={streamQuality}
                            onChange={(e) => handleQualityChange(e.target.value)}
                            className="px-4 py-2 border rounded text-gray-700"
                            disabled={!isStreamActive}
                        >
                            <option value="Alta">Calidad Alta</option>
                            <option value="Media">Calidad Media</option>
                            <option value="Baja">Calidad Baja</option>
                        </select>
                    </div>
                </div>

                {/* Alertas de detección */}
                {deteccion && deteccion.violencia_detectada && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <h2 className="text-xl font-semibold text-red-800 mb-2">🚨 Alerta de Violencia</h2>
                        <div className="text-red-700">
                            <p className="font-medium">
                                Probabilidad: {(deteccion.probabilidad * 100).toFixed(1)}%
                            </p>
                            <p>
                                Personas detectadas: {deteccion.personas_detectadas}
                            </p>
                            <p className="text-sm text-red-600 mt-1">
                                {new Date().toLocaleTimeString()} - Incidente registrado automáticamente
                            </p>
                        </div>
                    </div>
                )}

                {/* Detalles de la cámara */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Detalles de la Cámara</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-base">
                        {[
                            { label: "ID", value: cameraDetail.id },
                            { label: "Nombre", value: cameraDetail.nombre },
                            { label: "Ubicación", value: cameraDetail.ubicacion },
                            { label: "Descripción", value: cameraDetail.descripcion || "N/A" },
                            { label: "URL de Conexión", value: cameraDetail.url_conexion || "N/A" },
                            { label: "Tipo de Cámara", value: cameraDetail.tipo_camara.toUpperCase() },
                            { label: "Resolución", value: `${cameraDetail.resolucion_ancho}x${cameraDetail.resolucion_alto}` },
                            { label: "FPS", value: cameraDetail.fps },
                            { label: "Estado", value: cameraDetail.estado.charAt(0).toUpperCase() + cameraDetail.estado.slice(1) },
                            { label: "Configuración", value: JSON.stringify(cameraDetail.configuracion_json) },
                            { label: "Fecha de Instalación", value: new Date(cameraDetail.fecha_instalacion).toLocaleString() },
                            { label: "Última Actividad", value: new Date(cameraDetail.ultima_actividad).toLocaleString() },
                            { label: "Fecha de Creación", value: new Date(cameraDetail.fecha_creacion).toLocaleString() },
                            { label: "Última Actualización", value: new Date(cameraDetail.fecha_actualizacion).toLocaleString() },
                        ].map(({ label, value }, index) => (
                            <p key={index} className="text-gray-700">
                                <span className="font-bold">{label}:</span> 
                                <span className="font-normal ml-2">{value}</span>
                            </p>
                        ))}
                    </div>
                </div>

                {/* Información de rendimiento (solo visible en desarrollo) */}
                {process.env.NODE_ENV === 'development' && (
                    <div className="bg-gray-50 rounded-lg p-4 text-sm">
                        <h3 className="font-semibold text-gray-800 mb-2">Debug Info</h3>
                        <div className="grid grid-cols-2 gap-2 text-gray-600">
                            <span>Estado Stream: {isStreamActive ? 'Activo' : 'Inactivo'}</span>
                            <span>Estado Detección: {isDetectionActive ? 'Activa' : 'Inactiva'}</span>
                            <span>Conexión: {connectionStatus}</span>
                            <span>Calidad: {streamQuality}</span>
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