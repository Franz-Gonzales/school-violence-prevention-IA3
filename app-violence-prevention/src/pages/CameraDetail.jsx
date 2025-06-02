import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCameras, api } from '../utils/api';
import WebRTCClient from '../utils/webrtc';

const CameraDetail = () => {
    const { cameraId } = useParams();
    const navigate = useNavigate();
    const videoRef = useRef(null);

    const [cameraDetail, setCameraDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isStreamActive, setIsStreamActive] = useState(false);
    const [isDetectionActive, setIsDetectionActive] = useState(false);
    const [deteccion, setDeteccion] = useState(null);
    const [webRTCClient, setWebRTCClient] = useState(null);

    useEffect(() => {
        const fetchCamera = async () => {
            try {
                const cameras = await getCameras();
                const camera = cameras.find(cam => cam.id === Number(cameraId));
                if (!camera) { throw new Error('Cámara no encontrada'); }
                setCameraDetail(camera);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };
        fetchCamera();

        return () => {
            if (webRTCClient) {
                console.log('Limpiando recursos WebRTC...');
                webRTCClient.stop();
            }
        };
    }, [cameraId]);

    const handleDetection = (data) => {
        console.log('Datos de detección recibidos:', data);
        setDeteccion(data);

        // Solo actualizar el estado si hay una detección de violencia
        if (data.violencia_detectada) {
            // Mostrar alerta o actualizar UI
            console.log('¡ALERTA! Violencia detectada:', data.probabilidad);
        }
    };

    const handleToggleStream = async () => {
        try {
            if (!isStreamActive) {
                await api.post(`/api/v1/cameras/${cameraId}/activar`);
                const client = new WebRTCClient(cameraId, videoRef.current, handleDetection);
                await client.connect(false);
                setWebRTCClient(client);
                setIsStreamActive(true);
            } else {
                await api.post(`/api/v1/cameras/${cameraId}/desactivar`);
                if (webRTCClient) {
                    webRTCClient.stop();
                    setWebRTCClient(null);
                }
                setIsStreamActive(false);
                setIsDetectionActive(false);
                setDeteccion(null);
            }
        } catch (err) {
            setError(`Error al manejar stream: ${err.message}`);
            console.error(err);
        }
    };

    const handleToggleDetection = async () => {
        if (!webRTCClient) {
            setError('Debe iniciar el stream primero.');
            return;
        }

        try {
            if (!isDetectionActive) {
                console.log('Activando detección...');
                await api.post(`/api/v1/cameras/${cameraId}/activar`);
                webRTCClient.toggleDetection(true);
                setIsDetectionActive(true);
            } else {
                console.log('Desactivando detección...');
                webRTCClient.toggleDetection(false);
                setIsDetectionActive(false);
                setDeteccion(null);
            }
        } catch (err) {
            console.error('Error al cambiar estado de detección:', err);
            setError(`Error: ${err.message}`);
        }
    };

    if (loading) { return <p className="text-gray-600">Cargando detalles de la cámara...</p>; }
    if (error) { return <p className="text-red-600">Error: {error}</p>; }
    if (!cameraDetail) { return <p className="text-gray-600">Cámara no encontrada.</p>; }

    return (
        <div className="py-6 flex justify-center">
            <div className="w-full max-w-6xl flex flex-col space-y-2">
                <button
                    onClick={() => navigate('/cameras')}
                    className="mb-6 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm self-start"
                >
                    ← Volver a Cámaras
                </button>

                <div className="relative w-full bg-gray-200 rounded-lg flex items-center justify-center h-[720px]">
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover rounded-lg" />
                    <span
                        className={`absolute top-4 right-4 px-3 py-1 text-sm font-semibold rounded-full ${cameraDetail.estado === "activa"
                            ? "bg-green-500 text-white"
                            : cameraDetail.estado === "inactiva"
                                ? "bg-red-500 text-white"
                                : cameraDetail.estado === "mantenimiento"
                                    ? "bg-yellow-500 text-white"
                                    : "bg-gray-500 text-white"
                            }`}
                    >
                        {cameraDetail.estado.charAt(0).toUpperCase() + cameraDetail.estado.slice(1)}
                    </span>
                </div>

                <div className="bg-white rounded-lg shadow-md p-3">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Controles</h2>
                    <div className="flex justify-center space-x-5">
                        <button
                            onClick={handleToggleStream}
                            className={`px-6 py-2 rounded text-white ${isStreamActive ? "bg-red-500 hover:bg-red-600" : "bg-green-500 hover:bg-green-600"}`}
                            disabled={isDetectionActive}
                        >
                            {isStreamActive ? "Detener Stream" : "Iniciar Stream"}
                        </button>
                        <button
                            onClick={handleToggleDetection}
                            className={`px-6 py-2 rounded text-white ${isDetectionActive
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
                    </div>
                </div>

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
                                <span className="font-bold">{label}:</span> <span className="font-normal">{value}</span>
                            </p>
                        ))}
                    </div>
                </div>

                {deteccion && deteccion.violencia_detectada && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Alertas</h2>
                        <p className="text-sm text-red-600 mb-4">
                            Se ha detectado un incidente de violencia. Probabilidad: {(deteccion.probabilidad * 100).toFixed(2)}%
                            <br />
                            Personas involucradas: {deteccion.personas_detectadas}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CameraDetail;
