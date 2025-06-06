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
    
    // Estados del reproductor de video
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [playbackRate, setPlaybackRate] = useState(1);
    const [isFullscreen, setIsFullscreen] = useState(false);

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
            const response = await api.get(`/api/v1/incidents/${incidentId}`);
            setIncident(response.data);
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

    const changePlaybackRate = (rate) => {
        setPlaybackRate(rate);
        if (videoRef.current) {
            videoRef.current.playbackRate = rate;
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

    const skipTime = (seconds) => {
        if (videoRef.current) {
            const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
            videoRef.current.currentTime = newTime;
            setCurrentTime(newTime);
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
                return 'bg-red-500 text-white';
            case 'alta':
                return 'bg-orange-500 text-white';
            case 'media':
                return 'bg-yellow-500 text-white';
            case 'baja':
                return 'bg-green-500 text-white';
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
            second: '2-digit'
        });
    };

    const handleDownloadVideo = () => {
        if (incident?.video_evidencia_path) {
            const link = document.createElement('a');
            link.href = `${import.meta.env.VITE_API_URL}/evidencias/clips/${incident.video_evidencia_path.split('/').pop()}`;
            link.download = `evidencia_incidente_${incident.id}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const handleGenerateReport = () => {
        // Implementar generación de reporte
        alert('Funcionalidad de reporte en desarrollo');
    };

    const handleShareIncident = () => {
        // Implementar compartir incidente
        alert('Funcionalidad de compartir en desarrollo');
    };

    const handleMarkAsFalse = () => {
        // Implementar marcar como falso positivo
        alert('Funcionalidad de marcar como falso en desarrollo');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-white">
                <div className="flex justify-center items-center h-64">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                        <p className="text-gray-600">Cargando detalles del incidente...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !incident) {
        return (
            <div className="min-h-screen bg-white p-6">
                <div className="max-w-7xl mx-auto">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                        <p className="text-red-600">{error || 'Incidente no encontrado'}</p>
                        <button 
                            onClick={() => navigate('/incidents')}
                            className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                            Volver a Incidentes
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-white">
            <div className="max-w-7xl mx-auto p-6">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/incidents')}
                        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
                    >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Volver
                    </button>
                    
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Incidente #INC{String(incident.id).padStart(3, '0')}</h1>
                            <p className="text-gray-600 mt-1">Detalles completos del incidente registrado</p>
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(incident.severidad)}`}>
                                {incident.severidad?.charAt(0).toUpperCase() + incident.severidad?.slice(1)}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Video Player */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {incident.video_evidencia_path ? (
                                <>
                                    {/* Video Container */}
                                    <div className="relative bg-black" style={{ aspectRatio: '16/9' }}>
                                        <video
                                            ref={videoRef}
                                            className="w-full h-full object-contain"
                                            onPlay={() => setIsPlaying(true)}
                                            onPause={() => setIsPlaying(false)}
                                            onTimeUpdate={handleTimeUpdate}
                                            onLoadedMetadata={handleLoadedMetadata}
                                            onEnded={() => setIsPlaying(false)}
                                        >
                                            <source 
                                                src={`${import.meta.env.VITE_API_URL}/evidencias/clips/${incident.video_evidencia_path.split('/').pop()}`} 
                                                type="video/mp4" 
                                            />
                                            Tu navegador no soporta el elemento de video.
                                        </video>

                                        {/* Overlay de violencia detectada */}
                                        <div className="absolute top-4 left-4">
                                            <div className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium animate-pulse">
                                                Violencia Detectada
                                            </div>
                                        </div>

                                        {/* Información de confianza */}
                                        <div className="absolute top-4 right-4">
                                            <div className="bg-black bg-opacity-60 text-white px-3 py-1 rounded text-sm">
                                                Confianza: {incident.probabilidad_violencia ? (incident.probabilidad_violencia * 100).toFixed(1) : '92'}%
                                            </div>
                                        </div>

                                        {/* Timestamp del video */}
                                        <div className="absolute bottom-16 left-4">
                                            <div className="bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs font-mono">
                                                {incident.ubicacion} - {formatDate(incident.fecha_hora_inicio).split(',')[1]}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Controles del video */}
                                    <div className="bg-gray-900 text-white p-4">
                                        {/* Barra de progreso */}
                                        <div className="mb-3">
                                            <div 
                                                className="w-full h-2 bg-gray-700 rounded-full cursor-pointer"
                                                onClick={handleSeek}
                                            >
                                                <div 
                                                    className="h-full bg-red-500 rounded-full transition-all"
                                                    style={{ width: `${(currentTime / duration) * 100}%` }}
                                                />
                                            </div>
                                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                                                <span>{formatTime(currentTime)}</span>
                                                <span>{formatTime(duration)}</span>
                                            </div>
                                        </div>

                                        {/* Controles principales */}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-3">
                                                {/* Botón de reproducir/pausar */}
                                                <button 
                                                    onClick={togglePlay}
                                                    className="p-2 hover:bg-gray-800 rounded transition-colors"
                                                >
                                                    {isPlaying ? (
                                                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                                                        </svg>
                                                    ) : (
                                                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                                            <path d="M8 5v14l11-7z"/>
                                                        </svg>
                                                    )}
                                                </button>

                                                {/* Botones de salto */}
                                                <button 
                                                    onClick={() => skipTime(-10)}
                                                    className="p-1 hover:bg-gray-800 rounded transition-colors"
                                                    title="Retroceder 10s"
                                                >
                                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/>
                                                    </svg>
                                                </button>

                                                <button 
                                                    onClick={() => skipTime(10)}
                                                    className="p-1 hover:bg-gray-800 rounded transition-colors"
                                                    title="Avanzar 10s"
                                                >
                                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M18 13c0 3.31-2.69 6-6 6s-6-2.69-6-6 2.69-6 6-6v4l5-5-5-5v4c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8h-2z"/>
                                                    </svg>
                                                </button>

                                                {/* Control de volumen */}
                                                <div className="flex items-center space-x-2">
                                                    <button 
                                                        onClick={toggleMute}
                                                        className="p-1 hover:bg-gray-800 rounded transition-colors"
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
                                            </div>

                                            <div className="flex items-center space-x-3">
                                                {/* Velocidad de reproducción */}
                                                <div className="flex items-center space-x-1">
                                                    <span className="text-xs text-gray-400">Velocidad:</span>
                                                    <select 
                                                        value={playbackRate}
                                                        onChange={(e) => changePlaybackRate(parseFloat(e.target.value))}
                                                        className="bg-gray-800 text-white text-xs border border-gray-600 rounded px-2 py-1"
                                                    >
                                                        <option value={0.25}>0.25x</option>
                                                        <option value={0.5}>0.5x</option>
                                                        <option value={0.75}>0.75x</option>
                                                        <option value={1}>1x</option>
                                                        <option value={1.25}>1.25x</option>
                                                        <option value={1.5}>1.5x</option>
                                                        <option value={2}>2x</option>
                                                    </select>
                                                </div>

                                                {/* Pantalla completa */}
                                                <button 
                                                    onClick={toggleFullscreen}
                                                    className="p-1 hover:bg-gray-800 rounded transition-colors"
                                                    title="Pantalla completa"
                                                >
                                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex items-center justify-center h-96 bg-gray-100">
                                    <div className="text-center">
                                        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        </svg>
                                        <p className="text-gray-500">No hay video de evidencia disponible</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Acciones del video */}
                        <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">Acciones</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                <button
                                    onClick={handleDownloadVideo}
                                    className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Descargar Video
                                </button>

                                <button
                                    onClick={handleGenerateReport}
                                    className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                >
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Generar Reporte
                                </button>

                                <button
                                    onClick={handleShareIncident}
                                    className="flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                                >
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                                    </svg>
                                    Compartir
                                </button>

                                <button
                                    onClick={handleMarkAsFalse}
                                    className="flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                                >
                                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
                                    </svg>
                                    Marcar como Falso
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Panel de detalles */}
                    <div className="space-y-6">
                        {/* Información del incidente */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Detalles del Incidente</h2>
                            
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-500 mb-1">ID</label>
                                        <p className="text-gray-900 font-mono">INC{String(incident.id).padStart(3, '0')}</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-500 mb-1">Fecha y Hora</label>
                                        <p className="text-gray-900">{formatDate(incident.fecha_hora_inicio).split(' a las ')[0]}</p>
                                        <p className="text-gray-900">{formatDate(incident.fecha_hora_inicio).split(' a las ')[1]}</p>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 mb-1">Ubicación</label>
                                    <p className="text-gray-900">{incident.ubicacion}</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 mb-1">Severidad</label>
                                    <span className={`inline-flex px-2 py-1 text-sm font-semibold rounded-full ${getSeverityColor(incident.severidad)}`}>
                                        {incident.severidad?.charAt(0).toUpperCase() + incident.severidad?.slice(1)}
                                    </span>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 mb-1">Duración</label>
                                    <p className="text-gray-900">
                                        {incident.duracion_segundos ? `${incident.duracion_segundos} segundos` : '45 segundos'}
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 mb-1">Confianza de Detección</label>
                                    <div className="flex items-center">
                                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                                            <div 
                                                className="bg-red-500 h-2 rounded-full" 
                                                style={{ width: `${incident.probabilidad_violencia ? incident.probabilidad_violencia * 100 : 92}%` }}
                                            ></div>
                                        </div>
                                        <span className="ml-3 text-sm font-medium text-gray-900">
                                            {incident.probabilidad_violencia ? (incident.probabilidad_violencia * 100).toFixed(1) : '92'}%
                                        </span>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 mb-1">Descripción</label>
                                    <p className="text-gray-900">
                                        {incident.descripcion || 'Se detectó una pelea entre dos estudiantes en el pasillo principal. El personal intervino rápidamente para separar a los involucrados.'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Personas involucradas */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Personas Involucradas</h3>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div className="flex items-center">
                                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                                            P1
                                        </div>
                                        <span className="ml-3 text-gray-900">ID: P001</span>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div className="flex items-center">
                                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                                            P2
                                        </div>
                                        <span className="ml-3 text-gray-900">ID: P002</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Acciones tomadas */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Acciones Tomadas</h3>
                            <div className="space-y-3">
                                <div className="flex items-start">
                                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
                                    <div>
                                        <p className="text-gray-900 font-medium">Alerta sonora activada</p>
                                        <p className="text-gray-500 text-sm">Notificación enviada al personal</p>
                                    </div>
                                </div>
                                <div className="flex items-start">
                                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
                                    <div>
                                        <p className="text-gray-900 font-medium">Incidente registrado en el sistema</p>
                                        <p className="text-gray-500 text-sm">Alerta de emergencia enviada a seguridad</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Estilos personalizados para el slider */}
            <style jsx>{`
                .slider::-webkit-slider-thumb {
                    appearance: none;
                    width: 15px;
                    height: 15px;
                    border-radius: 50%;
                    background: #ef4444;
                    cursor: pointer;
                }
                .slider::-moz-range-thumb {
                    width: 15px;
                    height: 15px;
                    border-radius: 50%;
                    background: #ef4444;
                    cursor: pointer;
                    border: none;
                }
            `}</style>
        </div>
    );
};

export default IncidentDetail;