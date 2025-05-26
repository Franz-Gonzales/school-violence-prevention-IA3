import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const CameraDetail = () => {
    const { cameraId } = useParams();
    const navigate = useNavigate();

    // Datos estáticos basados en el modelo del backend
    const mockCameraDetail = {
        id: Number(cameraId),
        nombre: "Cámara Pasillo 1",
        ubicacion: "Pasillo Principal",
        descripcion: "Cámara de seguridad en el pasillo principal",
        url_conexion: "rtsp://example.com/stream1",
        tipo_camara: "rtsp",
        resolucion_ancho: 1280,
        resolucion_alto: 720,
        fps: 15,
        estado: "activa",
        configuracion_json: { quality: "high" },
        fecha_instalacion: "2024-01-15T10:00:00Z",
        ultima_actividad: "2025-05-26T16:30:00Z",
        fecha_creacion: "2024-01-10T08:00:00Z",
        fecha_actualizacion: "2025-05-26T16:30:00Z",
        deteccion: "Violencia detectada",
        incidenteId: 10,
    };

    // Estados para los controles (simulación estática)
    const [isCameraActive, setIsCameraActive] = useState(mockCameraDetail.estado === "activa");
    const [isDetectionActive, setIsDetectionActive] = useState(false);

    const handleToggleCamera = () => {
        setIsCameraActive(!isCameraActive);
        if (!isCameraActive) {
            // Simular activación
            mockCameraDetail.estado = "activa";
        } else {
            // Simular desactivación
            mockCameraDetail.estado = "inactiva";
            setIsDetectionActive(false); // Desactivar detección si se desactiva la cámara
        }
    };

    const handleToggleDetection = () => {
        if (!isCameraActive) return; // No hacer nada si la cámara no está activa
        setIsDetectionActive(!isDetectionActive);
    };

    const handleViewEvidence = () => {
        // Simular acción de ver evidencia
        alert(`Ver evidencia del incidente ${mockCameraDetail.incidenteId}`);
    };

    return (
        <div className="py-6 flex justify-center">
            <div className="w-full max-w-6xl flex flex-col space-y-6">
                {/* Botón para regresar */}
                <button
                    onClick={() => navigate('/cameras')}
                    className="mb-6 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm self-start"
                >
                    ← Volver a Cámaras
                </button>

                {/* Stream de la cámara */}
                <div className="relative w-full bg-gray-200 rounded-lg flex items-center justify-center h-[720px]">
                    <span className="text-gray-500 text-lg">Stream en vivo (Placeholder)</span>
                    <span
                        className={`absolute top-4 right-4 px-3 py-1 text-sm font-semibold rounded-full ${mockCameraDetail.estado === "activa"
                                ? "bg-green-500 text-white"
                                : mockCameraDetail.estado === "inactiva"
                                    ? "bg-red-500 text-white"
                                    : mockCameraDetail.estado === "mantenimiento"
                                        ? "bg-yellow-500 text-white"
                                        : "bg-gray-500 text-white"
                            }`}
                    >
                        {mockCameraDetail.estado.charAt(0).toUpperCase() + mockCameraDetail.estado.slice(1)}
                    </span>
                </div>

                {/* Controles */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Controles</h2>
                    <div className="flex justify-center space-x-4">
                        <button
                            onClick={handleToggleCamera}
                            className={`px-6 py-2 rounded text-white ${isCameraActive ? "bg-red-500 hover:bg-red-600" : "bg-green-500 hover:bg-green-600"
                                }`}
                        >
                            {isCameraActive ? "Detener Stream" : "Iniciar Stream"}
                        </button>
                        <button
                            onClick={handleToggleDetection}
                            className={`px-6 py-2 rounded text-white ${isDetectionActive
                                    ? "bg-red-500 hover:bg-red-600"
                                    : "bg-blue-500 hover:bg-blue-600"
                                } ${!isCameraActive ? "opacity-50 cursor-not-allowed" : ""}`}
                            disabled={!isCameraActive}
                        >
                            {isDetectionActive ? "Detener Detección" : "Iniciar Detección"}
                        </button>
                    </div>
                </div>

                {/* Detalles de la Cámara */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Detalles de la Cámara</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-base">
                        {[
                            { label: "ID", value: mockCameraDetail.id },
                            { label: "Nombre", value: mockCameraDetail.nombre },
                            { label: "Ubicación", value: mockCameraDetail.ubicacion },
                            { label: "Descripción", value: mockCameraDetail.descripcion || "N/A" },
                            { label: "URL de Conexión", value: mockCameraDetail.url_conexion || "N/A" },
                            { label: "Tipo de Cámara", value: mockCameraDetail.tipo_camara.toUpperCase() },
                            { label: "Resolución", value: `${mockCameraDetail.resolucion_ancho}x${mockCameraDetail.resolucion_alto}` },
                            { label: "FPS", value: mockCameraDetail.fps },
                            { label: "Estado", value: mockCameraDetail.estado.charAt(0).toUpperCase() + mockCameraDetail.estado.slice(1) },
                            { label: "Configuración", value: JSON.stringify(mockCameraDetail.configuracion_json) },
                            { label: "Fecha de Instalación", value: new Date(mockCameraDetail.fecha_instalacion).toLocaleString() },
                            { label: "Última Actividad", value: new Date(mockCameraDetail.ultima_actividad).toLocaleString() },
                            { label: "Fecha de Creación", value: new Date(mockCameraDetail.fecha_creacion).toLocaleString() },
                            { label: "Última Actualización", value: new Date(mockCameraDetail.fecha_actualizacion).toLocaleString() },
                        ].map(({ label, value }, index) => (
                            <p key={index} className="text-gray-700">
                                <span className="font-bold">{label}:</span> <span className="font-normal">{value}</span>
                            </p>
                        ))}
                    </div>
                </div>

                {/* Alertas */}
                {mockCameraDetail.deteccion === "Violencia detectada" && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Alertas</h2>
                        <p className="text-sm text-red-600 mb-4">
                            Se ha detectado un incidente de violencia.
                        </p>
                        <button
                            onClick={handleViewEvidence}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Ver Evidencia
                        </button>
                    </div>
                )}
            </div>
        </div>
    );

};

export default CameraDetail;