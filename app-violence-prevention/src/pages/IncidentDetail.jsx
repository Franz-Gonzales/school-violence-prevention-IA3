import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getIncident } from '../utils/api';

const IncidentDetail = () => {
    const { incidentId } = useParams();
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const videoRef = useRef(null);
    const playerContainerRef = useRef(null);

    const [incident, setIncident] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [videoError, setVideoError] = useState(null);

    // Estados del reproductor de video
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [videoLoaded, setVideoLoaded] = useState(false);
    const [showControls, setShowControls] = useState(true);
    const [isBuffering, setIsBuffering] = useState(false);

    // Estados específicos para Base64
    const [videoBase64, setVideoBase64] = useState(null);
    const [videoInfo, setVideoInfo] = useState(null);
    const [base64Loading, setBase64Loading] = useState(false);

    // Estados para animaciones
    const [fadeIn, setFadeIn] = useState(false);
    const [slideIn, setSlideIn] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        // Activar animaciones
        setTimeout(() => setFadeIn(true), 100);
        setTimeout(() => setSlideIn(true), 300);

        fetchIncidentDetail();
    }, [incidentId, isAuthenticated, navigate]);

    // Auto-hide controls
    useEffect(() => {
        let timeout;
        if (isPlaying && showControls) {
            timeout = setTimeout(() => setShowControls(false), 3000);
        }
        return () => clearTimeout(timeout);
    }, [isPlaying, showControls]);

    // Fullscreen change handler
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }, []);

    const fetchIncidentDetail = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log(`🔍 Obteniendo incidente ${incidentId} con Base64...`);

            const data = await getIncident(incidentId);
            console.log('📊 Datos del incidente recibidos:', data);

            setIncident(data);

            if (data.video_base64) {
                console.log(`🎥 Base64 encontrado: ${data.video_base64.length} caracteres`);

                const videoInfoData = {
                    duration: parseFloat(data.video_duration) || 0,
                    fps: parseInt(data.video_fps) || 15,
                    codec: data.video_codec || 'mp4v',
                    resolution: data.video_resolution || '640x480',
                    file_size: parseInt(data.video_file_size) || 0
                };

                setVideoInfo(videoInfoData);
                await processVideoBase64(data.video_base64, data.video_codec || 'mp4v');
            } else {
                console.log('⚠️ No hay video Base64 disponible para este incidente');
                setVideoError('No hay video disponible para este incidente');
            }

        } catch (err) {
            console.error('❌ Error obteniendo incidente:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const processVideoBase64 = async (base64Data, codec) => {
        try {
            setBase64Loading(true);
            console.log(`🔄 Procesando Base64: ${base64Data.length} caracteres`);

            if (!base64Data || base64Data.length < 100) {
                throw new Error('Datos de video Base64 inválidos');
            }

            let mimeType = 'video/mp4';

            if (codec) {
                console.log(`🎥 MIME Type: ${mimeType}`);
                console.log(`🎥 Codec reportado: ${codec}`);
            }

            const dataUrl = `data:${mimeType};base64,${base64Data}`;
            console.log(`🔗 Data URL creado: data:${mimeType};base64,[${base64Data.length} chars]`);

            setVideoBase64(dataUrl);
            setVideoError(null);

        } catch (err) {
            console.error('❌ Error procesando video Base64:', err);
            setVideoError(`Error procesando video: ${err.message}`);
        } finally {
            setBase64Loading(false);
        }
    };

    const togglePlay = () => {
        if (!videoRef.current) {
            return;
        }
        if (isPlaying) {
            videoRef.current.pause();
        } else {
            setIsBuffering(true);
            videoRef.current.play().catch(err => {
                console.error('Error reproduciendo video:', err);
                setVideoError('Error al reproducir el video');
                setIsBuffering(false);
            });
        }
    };

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
            setIsBuffering(false);
        }
    };

    const handleLoadedMetadata = () => {
        if (videoRef.current) {
            setDuration(videoRef.current.duration);
            setVideoLoaded(true);
            setIsBuffering(false);
            console.log('🎥 Video cargado - Duración:', videoRef.current.duration);
        }
    };

    const handleSeek = (e) => {
        if (!videoRef.current) {
            return;
        }
        const rect = e.currentTarget.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        const newTime = pos * duration;
        videoRef.current.currentTime = newTime;
        setCurrentTime(newTime);
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
        if (!videoRef.current) {
            return;
        }
        const newMuted = !isMuted;
        videoRef.current.muted = newMuted;
        setIsMuted(newMuted);

        if (newMuted) {
            setVolume(0);
        } else {
            setVolume(videoRef.current.volume || 1);
        }
    };

    const toggleFullscreen = async () => {
        if (!playerContainerRef.current) {
            return;
        }
        try {
            if (!isFullscreen) {
                if (playerContainerRef.current.requestFullscreen) {
                    await playerContainerRef.current.requestFullscreen();
                }
            } else {
                if (document.exitFullscreen) {
                    await document.exitFullscreen();
                }
            }
        } catch (error) {
            console.error('Error toggling fullscreen:', error);
        }
    };

    const formatTime = (time) => {
        if (!time || isNaN(time)) { return '0:00'; }

        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const handleDownloadVideo = () => {
        try {
            if (!videoBase64) {
                alert('No hay video disponible para descargar');
                return;
            }

            const link = document.createElement('a');
            link.href = videoBase64;
            link.download = `evidencia_incidente_${incidentId}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            console.log('📥 Descarga de video iniciada');
        } catch (err) {
            console.error('❌ Error descargando video:', err);
            alert('Error al descargar el video');
        }
    };

    const getSeverityColor = (severity) => {
        const colors = {
            'baja': 'from-yellow-400 to-yellow-600 text-white shadow-yellow-500/30',
            'media': 'from-orange-400 to-orange-600 text-white shadow-orange-500/30',
            'alta': 'from-red-400 to-red-600 text-white shadow-red-500/30',
            'critica': 'from-red-600 to-red-800 text-white shadow-red-600/40'
        };
        return colors[severity] || 'from-gray-400 to-gray-600 text-white shadow-gray-500/30';
    };

    const getStatusColor = (status) => {
        const colors = {
            'nuevo': 'from-blue-400 to-blue-600 text-white shadow-blue-500/30',
            'en_revision': 'from-yellow-400 to-yellow-600 text-white shadow-yellow-500/30',
            'confirmado': 'from-orange-400 to-orange-600 text-white shadow-orange-500/30',
            'falso_positivo': 'from-gray-400 to-gray-600 text-white shadow-gray-500/30',
            'resuelto': 'from-green-400 to-green-600 text-white shadow-green-500/30',
            'archivado': 'from-gray-300 to-gray-500 text-white shadow-gray-400/30'
        };
        return colors[status] || 'from-gray-400 to-gray-600 text-white shadow-gray-500/30';
    };

    const formatDate = (dateString) => {
        if (!dateString) { return 'No disponible'; }

        try {
            return new Date(dateString).toLocaleString('es-ES', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return 'Fecha inválida';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
                <div className="text-center">
                    <div className="relative">
                        <div className="animate-spin rounded-full h-24 w-24 border-4 border-gray-200 border-t-red-600 mx-auto mb-6"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-8 h-8 bg-red-600 rounded-full animate-pulse"></div>
                        </div>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-700 mb-2">Cargando detalles del incidente</h2>
                    <p className="text-gray-500">Por favor espere...</p>
                </div>
            </div>
        );
    }

    if (error || !incident) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100">
                <div className="text-center max-w-md mx-auto p-8 bg-white rounded-2xl shadow-xl">
                    <div className="text-red-600 text-6xl mb-6 animate-bounce">⚠️</div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">Error al cargar incidente</h1>
                    <p className="text-gray-600 mb-6">{error || 'Incidente no encontrado'}</p>
                    <button
                        onClick={() => navigate('/incidents')}
                        className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all transform hover:scale-105 shadow-lg"
                    >
                        🔙 Volver a incidentes
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 transition-all duration-1000 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
            <div className="container mx-auto px-4 py-8">
                {/* Header Mejorado */}
                <div className={`mb-8 transform transition-all duration-700 ${slideIn ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-6">
                            <button
                                onClick={() => navigate('/incidents')}
                                className="group flex items-center text-gray-600 hover:text-gray-900 transition-all transform hover:scale-105"
                            >
                                <div className="p-2 rounded-full bg-white shadow-md group-hover:shadow-lg transition-all mr-3">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                </div>
                                <span className="font-medium">Volver a incidentes</span>
                            </button>

                            <div className="flex items-center space-x-3">
                                <div className="p-3 bg-gradient-to-br from-red-500 to-red-600 rounded-full shadow-lg">
                                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                    </svg>
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-900 mb-1">
                                        Incidente #{incident.id}
                                    </h1>
                                    <p className="text-gray-600 text-sm">
                                        {formatDate(incident.fecha_hora_inicio)}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="flex space-x-3">
                            <span className={`px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r ${getSeverityColor(incident.severidad)} shadow-lg transform hover:scale-105 transition-all`}>
                                {incident.severidad?.toUpperCase()}
                            </span>
                            <span className={`px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r ${getStatusColor(incident.estado)} shadow-lg transform hover:scale-105 transition-all`}>
                                {incident.estado?.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                    {/* Video Player Mejorado - Más Grande */}
                    <div className={`xl:col-span-3 transform transition-all duration-700 delay-200 ${slideIn ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}>
                        <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200">
                            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                                <h2 className="text-xl font-bold text-white flex items-center">
                                    <div className="p-2 bg-white/20 rounded-lg mr-3">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    Video de Evidencia
                                </h2>
                            </div>

                            <div className="p-6">
                                {base64Loading && (
                                    <div className="flex items-center justify-center h-96 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl">
                                        <div className="text-center">
                                            <div className="relative mb-6">
                                                <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-300 border-t-red-600 mx-auto"></div>
                                                <div className="absolute inset-0 flex items-center justify-center">
                                                    <div className="w-6 h-6 bg-red-600 rounded-full animate-pulse"></div>
                                                </div>
                                            </div>
                                            <p className="text-gray-600 font-medium">Procesando video de evidencia...</p>
                                            <p className="text-gray-500 text-sm mt-1">Por favor espere</p>
                                        </div>
                                    </div>
                                )}

                                {videoError && (
                                    <div className="flex items-center justify-center h-96 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border-2 border-red-200">
                                        <div className="text-center">
                                            <div className="text-red-600 text-6xl mb-4 animate-pulse">📹</div>
                                            <h3 className="text-lg font-bold text-red-800 mb-2">Video no disponible</h3>
                                            <p className="text-red-700 font-medium">{videoError}</p>
                                        </div>
                                    </div>
                                )}

                                {videoBase64 && !base64Loading && !videoError && (
                                    <div className="space-y-6">
                                        {/* Video Player Container - MÁS GRANDE */}
                                        <div
                                            ref={playerContainerRef}
                                            className="relative bg-black rounded-xl overflow-hidden shadow-2xl group"
                                            style={{ aspectRatio: isFullscreen ? 'auto' : '16/10' }} // Aspect ratio más alto
                                            onMouseEnter={() => setShowControls(true)}
                                            onMouseMove={() => setShowControls(true)}
                                            onMouseLeave={() => !isPlaying || setShowControls(false)}
                                        >
                                            <video
                                                ref={videoRef}
                                                src={videoBase64}
                                                className={`w-full h-full object-contain ${isFullscreen ? 'h-screen' : 'min-h-[500px]'}`} // Altura mínima más grande
                                                onTimeUpdate={handleTimeUpdate}
                                                onLoadedMetadata={handleLoadedMetadata}
                                                onPlay={() => {
                                                    setIsPlaying(true);
                                                    setIsBuffering(false);
                                                }}
                                                onPause={() => setIsPlaying(false)}
                                                onWaiting={() => setIsBuffering(true)}
                                                onCanPlay={() => setIsBuffering(false)}
                                                onError={(e) => {
                                                    console.error('Error en video:', e);
                                                    setVideoError('Error al cargar el video');
                                                    setIsBuffering(false);
                                                }}
                                                preload="metadata"
                                            />

                                            {/* Loading Overlay */}
                                            {isBuffering && (
                                                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                                                    <div className="text-center">
                                                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-white/30 border-t-white mx-auto mb-2"></div>
                                                        <p className="text-white text-sm">Cargando...</p>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Play Button Overlay */}
                                            {!isPlaying && !isBuffering && (
                                                <div
                                                    className="absolute inset-0 flex items-center justify-center bg-black/30 cursor-pointer group-hover:bg-black/20 transition-all"
                                                    onClick={togglePlay}
                                                >
                                                    <div className="p-4 bg-white/90 rounded-full shadow-lg transform hover:scale-110 transition-all">
                                                        <svg className="w-12 h-12 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                                                            <path d="M8 5v14l11-7z" />
                                                        </svg>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Controls Overlay */}
                                            <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-6 transform transition-all duration-300 ${showControls ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0'
                                                }`}>
                                                {/* Progress Bar */}
                                                <div
                                                    className="w-full h-2 bg-white/20 rounded-full cursor-pointer mb-4 group hover:h-3 transition-all"
                                                    onClick={handleSeek}
                                                >
                                                    <div
                                                        className="h-full bg-gradient-to-r from-red-500 to-red-600 rounded-full relative group-hover:shadow-lg transition-all"
                                                        style={{ width: `${(currentTime / duration) * 100}%` }}
                                                    >
                                                        <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-all"></div>
                                                    </div>
                                                </div>

                                                {/* Controls */}
                                                <div className="flex items-center justify-between text-white">
                                                    <div className="flex items-center space-x-4">
                                                        <button
                                                            onClick={togglePlay}
                                                            className="p-2 hover:bg-white/20 rounded-full transition-all transform hover:scale-110"
                                                        >
                                                            {isPlaying ? (
                                                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                                                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                                                                </svg>
                                                            ) : (
                                                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                                                    <path d="M8 5v14l11-7z" />
                                                                </svg>
                                                            )}
                                                        </button>

                                                        <button
                                                            onClick={toggleMute}
                                                            className="p-2 hover:bg-white/20 rounded-full transition-all transform hover:scale-110"
                                                        >
                                                            {isMuted ? (
                                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                                                                </svg>
                                                            ) : (
                                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                                                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                                                                </svg>
                                                            )}
                                                        </button>

                                                        <div className="flex items-center space-x-2">
                                                            <input
                                                                type="range"
                                                                min="0"
                                                                max="1"
                                                                step="0.1"
                                                                value={volume}
                                                                onChange={handleVolumeChange}
                                                                className="w-20 h-1 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                                                            />
                                                        </div>

                                                        <span className="text-sm font-mono bg-black/30 px-2 py-1 rounded">
                                                            {formatTime(currentTime)} / {formatTime(duration)}
                                                        </span>
                                                    </div>

                                                    <div className="flex items-center space-x-2">
                                                        <button
                                                            onClick={handleDownloadVideo}
                                                            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg text-sm font-medium transition-all transform hover:scale-105 shadow-lg"
                                                        >
                                                            <svg className="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                            </svg>
                                                            Descargar
                                                        </button>

                                                        <button
                                                            onClick={toggleFullscreen}
                                                            className="p-2 hover:bg-white/20 rounded-full transition-all transform hover:scale-110"
                                                        >
                                                            {isFullscreen ? (
                                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5m11 5.5V4.5M15 9h4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5m11-5.5v4.5m0-4.5h4.5m0 0l-5.5 5.5" />
                                                                </svg>
                                                            ) : (
                                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                                                </svg>
                                                            )}
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Video Stats */}
                                        {videoInfo && (
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                {[
                                                    {
                                                        label: 'Duración',
                                                        value: `${typeof videoInfo.duration === 'number' ? videoInfo.duration.toFixed(1) : parseFloat(videoInfo.duration || 0).toFixed(1)}s`,
                                                        icon: '⏱️',
                                                        color: 'from-blue-500 to-blue-600'
                                                    },
                                                    {
                                                        label: 'FPS',
                                                        value: videoInfo.fps || 15,
                                                        icon: '🎬',
                                                        color: 'from-green-500 to-green-600'
                                                    },
                                                    {
                                                        label: 'Resolución',
                                                        value: videoInfo.resolution || '640x480',
                                                        icon: '📺',
                                                        color: 'from-purple-500 to-purple-600'
                                                    },
                                                    {
                                                        label: 'Tamaño',
                                                        value: videoInfo.file_size ? `${(videoInfo.file_size / 1024 / 1024).toFixed(1)} MB` : 'N/A',
                                                        icon: '💾',
                                                        color: 'from-orange-500 to-orange-600'
                                                    }
                                                ].map((stat, index) => (
                                                    <div
                                                        key={index}
                                                        className={`bg-gradient-to-br ${stat.color} p-4 rounded-xl shadow-lg text-white transform hover:scale-105 transition-all duration-300 hover:shadow-xl`}
                                                    >
                                                        <div className="flex items-center justify-between mb-2">
                                                            <span className="text-sm font-medium opacity-90">{stat.label}</span>
                                                            <span className="text-xl">{stat.icon}</span>
                                                        </div>
                                                        <div className="text-xl font-bold">{stat.value}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Información del incidente - Sidebar mejorado */}
                    <div className={`xl:col-span-1 space-y-6 transform transition-all duration-700 delay-400 ${slideIn ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}>
                        {/* Detalles básicos */}
                        <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
                            <div className="flex items-center mb-4">
                                <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg mr-3">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Detalles del Incidente</h3>
                            </div>

                            <div className="space-y-4">
                                {[
                                    {
                                        label: 'Tipo',
                                        value: incident.tipo_incidente?.replace('_', ' ') || 'No especificado',
                                        icon: '🚨'
                                    },
                                    {
                                        label: 'Ubicación',
                                        value: incident.ubicacion || 'No especificada',
                                        icon: '📍'
                                    },
                                    {
                                        label: 'Probabilidad',
                                        value: incident.probabilidad_violencia ? `${(parseFloat(incident.probabilidad_violencia) * 100).toFixed(1)}%` : 'N/A',
                                        icon: '📊'
                                    },
                                    {
                                        label: 'Personas Involucradas',
                                        value: incident.numero_personas_involucradas || 0,
                                        icon: '👥'
                                    }
                                ].map((item, index) => (
                                    <div key={index} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center">
                                                <span className="text-lg mr-2">{item.icon}</span>
                                                <label className="text-sm font-medium text-gray-600">{item.label}</label>
                                            </div>
                                        </div>
                                        <div className="text-base font-semibold text-gray-900 mt-1 capitalize">
                                            {item.value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Información temporal */}
                        <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
                            <div className="flex items-center mb-4">
                                <div className="p-2 bg-gradient-to-br from-green-500 to-green-600 rounded-lg mr-3">
                                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-bold text-gray-900">Información Temporal</h3>
                            </div>

                            <div className="space-y-4">
                                <div className="p-3 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                                    <label className="block text-sm font-medium text-blue-800 mb-1">📅 Fecha y Hora de Inicio</label>
                                    <div className="text-sm text-blue-900 font-medium">
                                        {formatDate(incident.fecha_hora_inicio)}
                                    </div>
                                </div>

                                {incident.fecha_hora_fin && (
                                    <div className="p-3 bg-gradient-to-r from-green-50 to-green-100 rounded-lg border border-green-200">
                                        <label className="block text-sm font-medium text-green-800 mb-1">✅ Finalizado</label>
                                        <div className="text-sm text-green-900 font-medium">
                                            {formatDate(incident.fecha_hora_fin)}
                                        </div>
                                    </div>
                                )}

                                {incident.duracion_segundos && (
                                    <div className="p-3 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border border-purple-200">
                                        <label className="block text-sm font-medium text-purple-800 mb-1">⏱️ Duración Total</label>
                                        <div className="text-sm text-purple-900 font-medium">
                                            {incident.duracion_segundos}s
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Descripción */}
                        {incident.descripcion && (
                            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
                                <div className="flex items-center mb-4">
                                    <div className="p-2 bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg mr-3">
                                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                                        </svg>
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900">Descripción</h3>
                                </div>
                                <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg">
                                    {incident.descripcion}
                                </p>
                            </div>
                        )}

                        {/* Metadata */}
                        {incident.metadata_json && (
                            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-200">
                                <div className="flex items-center mb-4">
                                    <div className="p-2 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg mr-3">
                                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                        </svg>
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900">Información Técnica</h3>
                                </div>
                                <div className="bg-gray-900 rounded-lg p-4 max-h-48 overflow-auto">
                                    <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                                        {JSON.stringify(incident.metadata_json, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* CSS personalizado para el slider */}
            <style jsx>{`
                .slider::-webkit-slider-thumb {
                    appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #ffffff;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
                    cursor: pointer;
                }
                
                .slider::-moz-range-thumb {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #ffffff;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
                    cursor: pointer;
                    border: none;
                }
            `}</style>
        </div>
    );
};

export default IncidentDetail;