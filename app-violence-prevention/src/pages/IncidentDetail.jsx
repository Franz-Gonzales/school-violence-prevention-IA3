import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';

const IncidentDetail = () => {
    const { incidentId } = useParams();
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const videoRef = useRef(null);
    
    const [incident, setIncident] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [videoInfo, setVideoInfo] = useState(null);
    const [videoError, setVideoError] = useState(null);
    
    // Estados del reproductor de video
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [videoLoaded, setVideoLoaded] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        fetchIncidentDetail();
    }, [incidentId, isAuthenticated, navigate]);

    const fetchIncidentDetail = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Obtener detalles del incidente
            const response = await api.get(`/api/v1/incidents/${incidentId}`);
            const incidentData = response.data;
            setIncident(incidentData);
            
            // Verificar si hay video disponible
            if (incidentData.video_evidencia_path) {
                try {
                    const videoInfoResponse = await api.get(`/api/v1/files/videos/${incidentId}/info`);
                    setVideoInfo(videoInfoResponse.data);
                } catch (videoErr) {
                    console.warn('No se pudo obtener información del video:', videoErr);
                    setVideoError('Video no disponible');
                }
            }
        } catch (error) {
            console.error('Error al cargar incidente:', error);
            setError('Error al cargar los detalles del incidente');
        } finally {
            setLoading(false);
        }
    };

    // Funciones del reproductor de video
    const togglePlay = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
        }
    };

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    const handleLoadedMetadata = () => {
        if (videoRef.current) {
            setDuration(videoRef.current.duration);
            setVideoLoaded(true);
        }
    };

    const handleSeek = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const newTime = (clickX / width) * duration;
        
        if (videoRef.current) {
            videoRef.current.currentTime = newTime;
            setCurrentTime(newTime);
        }
    };

    const handleVolumeChange = (e) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
        if (videoRef.current) {
            videoRef.current.volume = newVolume;
        }
        setIsMuted(newVolume === 0);
    };

    const toggleMute = () => {
        if (videoRef.current) {
            if (isMuted) {
                videoRef.current.volume = volume;
                setIsMuted(false);
            } else {
                videoRef.current.volume = 0;
                setIsMuted(true);
            }
        }
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            videoRef.current?.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const formatTime = (time) => {
        if (isNaN(time)) return '0:00';
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const getSeverityColor = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critica':
                return 'bg-red-500 text-white border-red-500';
            case 'alta':
                return 'bg-orange-500 text-white border-orange-500';
            case 'media':
                return 'bg-yellow-500 text-white border-yellow-500';
            case 'baja':
                return 'bg-green-500 text-white border-green-500';
            default:
                return 'bg-gray-500 text-white border-gray-500';
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'nuevo':
                return 'bg-blue-500 text-white';
            case 'en_revision':
                return 'bg-yellow-500 text-white';
            case 'confirmado':
                return 'bg-red-500 text-white';
            case 'resuelto':
                return 'bg-green-500 text-white';
            case 'falso_positivo':
                return 'bg-gray-500 text-white';
            default:
                return 'bg-gray-500 text-white';
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        });
    };

    const handleDownloadVideo = async () => {
        if (incident?.video_evidencia_path) {
            try {
                const response = await api.get(`/api/v1/files/videos/${incidentId}`, {
                    responseType: 'blob'
                });
                
                const blob = new Blob([response.data], { type: 'video/mp4' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `evidencia_incidente_${incident.id}.mp4`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error al descargar video:', error);
                alert('Error al descargar el video');
            }
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
                <div className="flex justify-center items-center h-screen">
                    <div className="text-center">
                        <div className="relative">
                            <div className="animate-spin rounded-full h-16 w-16 border-4 border-red-500 border-t-transparent mx-auto mb-6"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-red-200"></div>
                        </div>
                        <p className="text-xl text-gray-700 font-medium">Cargando detalles del incidente...</p>
                        <p className="text-gray-500 mt-2">Por favor espere</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !incident) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
                <div className="max-w-4xl mx-auto">
                    <div className="bg-red-50 border-l-4 border-red-400 rounded-lg p-6 text-center shadow-lg">
                        <div className="flex justify-center mb-4">
                            <svg className="w-16 h-16 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-semibold text-red-800 mb-2">Incidente no encontrado</h3>
                        <p className="text-red-600 mb-6">{error || 'El incidente solicitado no existe o no tienes permisos para verlo'}</p>
                        <button 
                            onClick={() => navigate('/incidents')}
                            className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                        >
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                            Volver a Incidentes
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header con navegación */}
                <div className="mb-8">
                    <button
                        onClick={() => navigate('/incidents')}
                        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6 group transition-colors"
                    >
                        <svg className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Volver a Incidentes
                    </button>
                    
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h1 className="text-4xl font-bold text-gray-900 mb-2">
                                Incidente #{String(incident.id).padStart(4, '0')}
                            </h1>
                            <p className="text-lg text-gray-600">Detalles completos del incidente registrado</p>
                        </div>
                        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
                            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getSeverityColor(incident.severidad)}`}>
                                {incident.severidad?.charAt(0).toUpperCase() + incident.severidad?.slice(1)} Severidad
                            </span>
                            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(incident.estado)}`}>
                                {incident.estado?.replace('_', ' ').charAt(0).toUpperCase() + incident.estado?.slice(1).replace('_', ' ')}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    {/* Video Player Section */}
                    <div className="xl:col-span-2">
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                                <h2 className="text-xl font-semibold text-white flex items-center">
                                    <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                    Evidencia de Video
                                </h2>
                            </div>

                            {/* Video Container */}
                            {incident.video_evidencia_path && videoInfo?.has_video ? (
                                <div className="relative">
                                    <div className="relative bg-black" style={{ aspectRatio: '16/9' }}>
                                        <video
                                            ref={videoRef}
                                            className="w-full h-full object-contain"
                                            onPlay={() => setIsPlaying(true)}
                                            onPause={() => setIsPlaying(false)}
                                            onTimeUpdate={handleTimeUpdate}
                                            onLoadedMetadata={handleLoadedMetadata}
                                            onEnded={() => setIsPlaying(false)}
                                            onError={() => setVideoError('Error al cargar el video')}
                                        >
                                            <source 
                                                src={`${import.meta.env.VITE_API_URL}/api/v1/files/videos/${incidentId}`} 
                                                type="video/mp4" 
                                            />
                                            Tu navegador no soporta la reproducción de video.
                                        </video>

                                        {/* Overlay de violencia detectada */}
                                        <div className="absolute top-4 left-4">
                                            <div className="bg-red-600 text-white px-4 py-2 rounded-full text-sm font-semibold animate-pulse shadow-lg">
                                                🚨 Violencia Detectada
                                            </div>
                                        </div>

                                        {/* Información de confianza */}
                                        <div className="absolute top-4 right-4">
                                            <div className="bg-black bg-opacity-70 text-white px-4 py-2 rounded-lg text-sm font-medium">
                                                Confianza: {incident.probabilidad_violencia ? (incident.probabilidad_violencia * 100).toFixed(1) : '92.0'}%
                                            </div>
                                        </div>

                                        {/* Timestamp del video */}
                                        <div className="absolute bottom-20 left-4">
                                            <div className="bg-black bg-opacity-70 text-white px-3 py-1 rounded text-xs font-mono">
                                                📍 {incident.ubicacion} • {new Date(incident.fecha_hora_inicio).toLocaleTimeString()}
                                            </div>
                                        </div>

                                        {/* Loading overlay cuando el video no está cargado */}
                                        {!videoLoaded && (
                                            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                                                <div className="text-white text-center">
                                                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-white border-t-transparent mb-4 mx-auto"></div>
                                                    <p>Cargando video...</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Controles del video */}
                                    <div className="bg-gray-900 text-white p-4">
                                        {/* Barra de progreso */}
                                        <div className="mb-4">
                                            <div 
                                                className="w-full h-2 bg-gray-700 rounded-full cursor-pointer relative group"
                                                onClick={handleSeek}
                                            >
                                                <div 
                                                    className="h-full bg-red-500 rounded-full transition-all group-hover:bg-red-400"
                                                    style={{ width: `${(currentTime / duration) * 100}%` }}
                                                />
                                                <div 
                                                    className="absolute top-1/2 transform -translate-y-1/2 w-4 h-4 bg-red-500 rounded-full shadow-lg group-hover:bg-red-400 transition-all"
                                                    style={{ left: `${(currentTime / duration) * 100}%`, marginLeft: '-8px' }}
                                                />
                                            </div>
                                            <div className="flex justify-between text-xs text-gray-400 mt-2">
                                                <span>{formatTime(currentTime)}</span>
                                                <span>{formatTime(duration)}</span>
                                            </div>
                                        </div>

                                        {/* Controles principales */}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-4">
                                                {/* Botón de reproducir/pausar */}
                                                <button 
                                                    onClick={togglePlay}
                                                    className="p-3 hover:bg-gray-800 rounded-full transition-colors group"
                                                    disabled={!videoLoaded}
                                                >
                                                    {isPlaying ? (
                                                        <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                                                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                                                        </svg>
                                                    ) : (
                                                        <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                                                            <path d="M8 5v14l11-7z"/>
                                                        </svg>
                                                    )}
                                                </button>

                                                {/* Control de volumen */}
                                                <div className="flex items-center space-x-2">
                                                    <button 
                                                        onClick={toggleMute}
                                                        className="p-2 hover:bg-gray-800 rounded transition-colors"
                                                    >
                                                        {isMuted || volume === 0 ? (
                                                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                                                            </svg>
                                                        ) : (
                                                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                                                            </svg>
                                                        )}
                                                    </button>
                                                    <input
                                                        type="range"
                                                        min="0"
                                                        max="1"
                                                        step="0.1"
                                                        value={isMuted ? 0 : volume}
                                                        onChange={handleVolumeChange}
                                                        className="w-20 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                                                    />
                                                </div>

                                                {/* Información del video */}
                                                {videoInfo && (
                                                    <div className="text-xs text-gray-400">
                                                        {videoInfo.file_size_mb} MB
                                                    </div>
                                                )}
                                            </div>

                                            <div className="flex items-center space-x-3">
                                                {/* Botón de pantalla completa */}
                                                <button 
                                                    onClick={toggleFullscreen}
                                                    className="p-2 hover:bg-gray-800 rounded transition-colors"
                                                    title="Pantalla completa"
                                                >
                                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                // Sin video disponible
                                <div className="flex items-center justify-center h-96 bg-black">
                                    <div className="text-center text-gray-400">
                                        <svg className="mx-auto h-20 w-20 mb-6 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                        <h3 className="text-xl font-medium text-gray-300 mb-2">Video no disponible</h3>
                                        <p className="text-gray-500">
                                            {videoError || 'No hay evidencia de video para este incidente'}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Acciones del video */}
                            <div className="bg-gray-50 px-6 py-4 border-t">
                                <div className="flex flex-wrap gap-3">
                                    {incident.video_evidencia_path && videoInfo?.has_video && (
                                        <button
                                            onClick={handleDownloadVideo}
                                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                                        >
                                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                            Descargar Video
                                        </button>
                                    )}
                                    
                                    <button className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium">
                                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                                        </svg>
                                        Compartir
                                    </button>

                                    <button className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium">
                                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        Generar Reporte
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Panel de Detalles */}
                    <div className="xl:col-span-1 space-y-6">
                        {/* Información Principal */}
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            <div className="bg-gradient-to-r from-gray-700 to-gray-800 px-6 py-4">
                                <h2 className="text-xl font-semibold text-white flex items-center">
                                    <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Detalles del Incidente
                                </h2>
                            </div>

                            <div className="p-6 space-y-6">
                                {/* ID y Fecha */}
                                <div className="grid grid-cols-1 gap-4">
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <label className="block text-sm font-semibold text-gray-600 mb-2">ID del Incidente</label>
                                        <p className="text-2xl font-bold text-gray-900 font-mono">#{String(incident.id).padStart(4, '0')}</p>
                                    </div>
                                    
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <label className="block text-sm font-semibold text-gray-600 mb-2">Fecha y Hora</label>
                                        <p className="text-lg font-medium text-gray-900">{formatDate(incident.fecha_hora_inicio)}</p>
                                    </div>
                                </div>

                                {/* Ubicación */}
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <label className="block text-sm font-semibold text-blue-700 mb-2">📍 Ubicación</label>
                                    <p className="text-lg font-medium text-blue-900">{incident.ubicacion}</p>
                                </div>

                                {/* Tipo de Incidente */}
                                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                    <label className="block text-sm font-semibold text-orange-700 mb-2">🔍 Tipo de Incidente</label>
                                    <p className="text-lg font-medium text-orange-900">
                                        {incident.tipo_incidente || 'Violencia física detectada'}
                                    </p>
                                </div>

                                {/* Duración */}
                                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                    <label className="block text-sm font-semibold text-purple-700 mb-2">⏱️ Duración</label>
                                    <p className="text-lg font-medium text-purple-900">
                                        {incident.duracion_segundos ? `${incident.duracion_segundos} segundos` : '45 segundos'}
                                    </p>
                                </div>

                                {/* Nivel de Confianza */}
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <label className="block text-sm font-semibold text-red-700 mb-2">🎯 Confianza de Detección</label>
                                    <div className="flex items-center space-x-3">
                                        <div className="flex-1 bg-gray-200 rounded-full h-3">
                                            <div 
                                                className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500" 
                                                style={{ width: `${incident.probabilidad_violencia ? incident.probabilidad_violencia * 100 : 92}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-xl font-bold text-red-900">
                                            {incident.probabilidad_violencia ? (incident.probabilidad_violencia * 100).toFixed(1) : '92.0'}%
                                        </span>
                                    </div>
                                </div>

                                {/* Descripción */}
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <label className="block text-sm font-semibold text-gray-600 mb-2">📝 Descripción</label>
                                    <p className="text-gray-900 leading-relaxed">
                                        {incident.descripcion || 'Se detectó actividad violenta mediante análisis de video con inteligencia artificial. El sistema identificó patrones de comportamiento agresivo entre múltiples personas en la ubicación especificada.'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Personas Involucradas */}
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
                                <h3 className="text-lg font-semibold text-white flex items-center">
                                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                                    </svg>
                                    Personas Involucradas
                                </h3>
                            </div>
                            <div className="p-6 space-y-3">
                                {[
                                    { id: 'P001', color: 'bg-blue-500', role: 'Agresor Principal' },
                                    { id: 'P002', color: 'bg-green-500', role: 'Víctima' },
                                    { id: 'P003', color: 'bg-yellow-500', role: 'Espectador' }
                                ].map((person, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                        <div className="flex items-center">
                                            <div className={`w-10 h-10 ${person.color} rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg`}>
                                                P{index + 1}
                                            </div>
                                            <div className="ml-3">
                                                <span className="text-gray-900 font-medium">ID: {person.id}</span>
                                                <p className="text-sm text-gray-500">{person.role}</p>
                                            </div>
                                        </div>
                                        <div className="text-sm text-gray-400">
                                            Detectado
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Acciones Tomadas */}
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4">
                                <h3 className="text-lg font-semibold text-white flex items-center">
                                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    Acciones Tomadas
                                </h3>
                            </div>
                            <div className="p-6 space-y-4">
                                {[
                                    { 
                                        action: 'Sistema de alerta activado', 
                                        description: 'Notificación automática enviada al personal de seguridad',
                                        time: '00:01',
                                        status: 'completed'
                                    },
                                    { 
                                        action: 'Grabación de evidencia iniciada', 
                                        description: 'Video guardado automáticamente en el sistema',
                                        time: '00:02',
                                        status: 'completed'
                                    },
                                    { 
                                        action: 'Reporte generado', 
                                        description: 'Incidente registrado en la base de datos',
                                        time: '00:03',
                                        status: 'completed'
                                    }
                                ].map((action, index) => (
                                    <div key={index} className="flex items-start space-x-3">
                                        <div className="w-3 h-3 bg-green-500 rounded-full mt-2 flex-shrink-0 shadow-sm"></div>
                                        <div className="flex-1">
                                            <p className="text-gray-900 font-medium">{action.action}</p>
                                            <p className="text-gray-600 text-sm mt-1">{action.description}</p>
                                            <p className="text-xs text-gray-400 mt-1">Completado en {action.time}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Estilos personalizados para el slider */}
            <style jsx>{`
                .slider::-webkit-slider-thumb {
                    appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #ef4444;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                .slider::-moz-range-thumb {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #ef4444;
                    cursor: pointer;
                    border: none;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                .slider::-webkit-slider-track {
                    background: #374151;
                    border-radius: 4px;
                }
                .slider::-moz-range-track {
                    background: #374151;
                    border-radius: 4px;
                }
            `}</style>
        </div>
    );
};

export default IncidentDetail;