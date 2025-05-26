import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/ui/Card';

const Cameras = () => {
    const navigate = useNavigate();

    // Datos estáticos basados en el modelo del backend
    const mockCameras = [
        {
            id: 1,
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
        },
        {
            id: 2,
            nombre: "Cámara Patio",
            ubicacion: "Patio Central",
            descripcion: "Cámara en el patio central",
            url_conexion: "rtsp://example.com/stream2",
            tipo_camara: "ip",
            resolucion_ancho: 1280,
            resolucion_alto: 720,
            fps: 30,
            estado: "inactiva",
            configuracion_json: { quality: "medium" },
            fecha_instalacion: "2024-02-20T09:00:00Z",
            ultima_actividad: "2025-05-25T12:00:00Z",
            fecha_creacion: "2024-02-15T07:00:00Z",
            fecha_actualizacion: "2025-05-25T12:00:00Z",
        },
        {
            id: 3,
            nombre: "Cámara Entrada",
            ubicacion: "Entrada Principal",
            descripcion: "Cámara en la entrada principal",
            url_conexion: "rtsp://example.com/stream3",
            tipo_camara: "rtsp",
            resolucion_ancho: 1920,
            resolucion_alto: 1080,
            fps: 15,
            estado: "mantenimiento",
            configuracion_json: { quality: "high" },
            fecha_instalacion: "2024-03-10T11:00:00Z",
            ultima_actividad: "2025-05-20T10:00:00Z",
            fecha_creacion: "2024-03-05T06:00:00Z",
            fecha_actualizacion: "2025-05-20T10:00:00Z",
        },
        {
            id: 4,
            nombre: "Cámara Aula 101",
            ubicacion: "Aula 101",
            descripcion: "Cámara en el aula 101",
            url_conexion: "rtsp://example.com/stream4",
            tipo_camara: "usb",
            resolucion_ancho: 1280,
            resolucion_alto: 720,
            fps: 15,
            estado: "activa",
            configuracion_json: { quality: "low" },
            fecha_instalacion: "2024-04-01T08:00:00Z",
            ultima_actividad: "2025-05-26T15:00:00Z",
            fecha_creacion: "2024-03-30T09:00:00Z",
            fecha_actualizacion: "2025-05-26T15:00:00Z",
        },
    ];

    return (
        <div className="py-6">
            <h1 className="text-2xl font-bold text-primary mb-6">Monitoreo de Cámaras</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {mockCameras.length > 0 ? (
                    mockCameras.map((camera) => (
                        <Card key={camera.id} className="flex flex-col">
                            {/* Placeholder para el video - Más grande */}
                            <div className="relative w-full h-80 bg-gray-200 rounded-t-lg flex items-center justify-center">
                                <span className="text-gray-500 text-lg">
                                    Stream en vivo (Placeholder)
                                </span>
                                {/* Indicador de estado */}
                                <span
                                    className={`absolute top-4 right-4 px-3 py-1 text-sm font-semibold rounded-full ${
                                        camera.estado === "activa"
                                            ? "bg-green-500 text-white"
                                            : camera.estado === "inactiva"
                                            ? "bg-red-500 text-white"
                                            : camera.estado === "mantenimiento"
                                            ? "bg-yellow-500 text-white"
                                            : "bg-gray-500 text-white"
                                    }`}
                                >
                                    {camera.estado.charAt(0).toUpperCase() + camera.estado.slice(1)}
                                </span>
                            </div>
                            {/* Información de la cámara */}
                            <div className="p-6">
                                <h3 className="text-xl font-semibold text-gray-900">{camera.nombre}</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                    Ubicación: {camera.ubicacion}
                                </p>
                                <p className="text-sm text-gray-600">
                                    Tipo: {camera.tipo_camara.toUpperCase()}
                                </p>
                                <button
                                    onClick={() => navigate(`/cameras/${camera.id}`)}
                                    className="mt-4 w-full px-4 py-2 bg-primary text-white rounded hover:bg-secondary text-sm"
                                >
                                    Ver Detalles
                                </button>
                            </div>
                        </Card>
                    ))
                ) : (
                    <p className="text-gray-600">No hay cámaras registradas.</p>
                )}
            </div>
        </div>
    );
};

export default Cameras;