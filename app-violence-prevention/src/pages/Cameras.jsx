// pages/cameras.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/ui/Card';
import { getCameras } from '../utils/api';

const Cameras = () => {
    const navigate = useNavigate();
    const [cameras, setCameras] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCameras = async () => {
            try {
                const data = await getCameras(false); // Solo cámaras activas
                setCameras(data);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };
        fetchCameras();
    }, []);

    return (
        <div className="py-6">
            <h1 className="text-2xl font-bold text-primary mb-6">Monitoreo de Cámaras</h1>
            
            {loading ? (
                <p className="text-gray-600">Cargando cámaras...</p>
            ) : error ? (
                <p className="text-red-600">Error: {error}</p>
            ) : cameras.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {cameras.map((camera) => (
                        <Card key={camera.id} className="flex flex-col">
                            <div className="relative w-full h-80 bg-gray-200 rounded-t-lg flex items-center justify-center">
                                <span className="text-gray-500 text-lg">
                                    Stream en vivo (Placeholder)
                                </span>
                                <span
                                    className={`absolute top-4 right-4 px-3 py-1 text-sm font-semibold rounded-full ${camera.estado === "activa"
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
                    ))}
                </div>
            ) : (
                <div className="text-center">
                    <p className="text-gray-600 mb-4">No hay cámaras registradas.</p>
                    <p className="text-sm text-gray-500">
                        Contacta al administrador para agregar cámaras al sistema.
                    </p>
                </div>
            )}
        </div>
    );
};

export default Cameras;