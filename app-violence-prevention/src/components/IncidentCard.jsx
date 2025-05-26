import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from './ui/Card';

const IncidentCard = ({ incident }) => {
    const navigate = useNavigate();

    const handleViewCamera = () => {
        // Redirigir a la página de cámaras con el ID de la cámara
        navigate(`/cameras/${incident.camara_id}`);
    };

    return (
        <Card className="flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-gray-900">
                    {incident.tipo_incidente} - {incident.ubicacion}
                </p>
                <p className="text-xs text-gray-500">
                    {new Date(incident.fecha_hora_inicio).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">
                    Severidad: {incident.severidad}
                </p>
            </div>
            <button
                onClick={handleViewCamera}
                className="px-3 py-1 bg-primary text-white rounded hover:bg-secondary text-sm"
            >
                Ver Cámara
            </button>
        </Card>
    );
};

export default IncidentCard;