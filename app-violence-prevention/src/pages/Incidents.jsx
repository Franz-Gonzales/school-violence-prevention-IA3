import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getIncidents } from '../utils/api';
import IncidentCard from '../components/IncidentCard';

const Incidents = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [incidents, setIncidents] = useState([]);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        const fetchIncidents = async () => {
            try {
                const data = await getIncidents({ limite: 20 });
                setIncidents(data);
            } catch (error) {
                console.error('Error al cargar incidentes:', error);
            }
        };

        fetchIncidents();
    }, [isAuthenticated, navigate]);

    return (
        <div className="py-6">
            <h1 className="text-2xl font-bold text-primary mb-4">Incidentes</h1>
            <div className="space-y-4">
                {incidents.length > 0 ? (
                    incidents.map((incident) => (
                        <IncidentCard key={incident.id} incident={incident} />
                    ))
                ) : (
                    <p className="text-gray-600">No hay incidentes registrados.</p>
                )}
            </div>
        </div>
    );
};

export default Incidents;