import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getIncidents } from '../utils/api';

const Incidents = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Estados para filtros y búsqueda
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedSeverity, setSelectedSeverity] = useState('');
    const [selectedLocation, setSelectedLocation] = useState('');
    const [selectedDateRange, setSelectedDateRange] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        fetchIncidents();
    }, [isAuthenticated, navigate]);

    const fetchIncidents = async () => {
        try {
            setLoading(true);
            const data = await getIncidents({ limite: 100 });
            setIncidents(data || []);
        } catch (error) {
            console.error('Error al cargar incidentes:', error);
            setError('Error al cargar los incidentes');
        } finally {
            setLoading(false);
        }
    };

    // Función para filtrar incidentes
    const filteredIncidents = incidents.filter(incident => {
        const matchesSearch = incident.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             incident.ubicacion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             incident.tipo_incidente?.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesSeverity = !selectedSeverity || incident.severidad === selectedSeverity;
        const matchesLocation = !selectedLocation || incident.ubicacion === selectedLocation;
        
        return matchesSearch && matchesSeverity && matchesLocation;
    });

    // Paginación
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentIncidents = filteredIncidents.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(filteredIncidents.length / itemsPerPage);

    // Obtener ubicaciones únicas para el filtro
    const uniqueLocations = [...new Set(incidents.map(inc => inc.ubicacion).filter(Boolean))];

    const getSeverityColor = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critica':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'alta':
                return 'bg-orange-100 text-orange-800 border-orange-200';
            case 'media':
                return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'baja':
                return 'bg-green-100 text-green-800 border-green-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'nuevo':
                return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'en_revision':
                return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'confirmado':
                return 'bg-red-100 text-red-800 border-red-200';
            case 'resuelto':
                return 'bg-green-100 text-green-800 border-green-200';
            case 'falso_positivo':
                return 'bg-gray-100 text-gray-800 border-gray-200';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatIncidentType = (type) => {
        const types = {
            'pelea': 'Pelea entre estudiantes',
            'violencia_fisica': 'Agresión física en el patio',
            'multitud_agresiva': 'Discusión acalorada'
        };
        return types[type] || type;
    };

    const handleViewIncident = (incidentId) => {
        navigate(`/incidents/${incidentId}`);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-white">
                <div className="flex justify-center items-center h-64">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                        <p className="text-gray-600">Cargando incidentes...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-white p-6">
                <div className="max-w-7xl mx-auto">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                        <p className="text-red-600">{error}</p>
                        <button 
                            onClick={fetchIncidents}
                            className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                            Reintentar
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
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">Registro de Incidentes</h1>
                            <p className="text-gray-600">Historial de eventos de violencia detectados por el sistema</p>
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className="flex items-center text-sm text-gray-500">
                                <div className="w-2 h-2 rounded-full bg-red-500 mr-2"></div>
                                {incidents.filter(inc => inc.estado === 'nuevo').length}
                            </span>
                            <button 
                                onClick={fetchIncidents}
                                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Actualizar
                            </button>
                        </div>
                    </div>
                </div>

                {/* Filtros */}
                <div className="bg-gray-50 rounded-lg p-6 mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {/* Búsqueda */}
                        <div className="relative">
                            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                type="text"
                                placeholder="Buscar incidentes..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            />
                        </div>

                        {/* Filtro por Fecha */}
                        <div>
                            <select
                                value={selectedDateRange}
                                onChange={(e) => setSelectedDateRange(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            >
                                <option value="">Fecha</option>
                                <option value="today">Hoy</option>
                                <option value="week">Esta semana</option>
                                <option value="month">Este mes</option>
                            </select>
                        </div>

                        {/* Filtro por Severidad */}
                        <div>
                            <select
                                value={selectedSeverity}
                                onChange={(e) => setSelectedSeverity(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            >
                                <option value="">Severidad</option>
                                <option value="critica">Crítica</option>
                                <option value="alta">Alta</option>
                                <option value="media">Media</option>
                                <option value="baja">Baja</option>
                            </select>
                        </div>

                        {/* Filtro por Ubicación */}
                        <div>
                            <select
                                value={selectedLocation}
                                onChange={(e) => setSelectedLocation(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                            >
                                <option value="">Ubicación</option>
                                {uniqueLocations.map(location => (
                                    <option key={location} value={location}>{location}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Tabla de Incidentes */}
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Incidente
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Ubicación
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Fecha y Hora
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Severidad
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Estado
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Acciones
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {currentIncidents.length > 0 ? (
                                    currentIncidents.map((incident) => (
                                        <tr key={incident.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                INC{String(incident.id).padStart(3, '0')}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center">
                                                    <div className="text-red-500 text-lg mr-3">
                                                        {incident.severidad === 'critica' ? '🚨' : 
                                                         incident.severidad === 'alta' ? '⚠️' : '⚡'}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-gray-900">
                                                            {formatIncidentType(incident.tipo_incidente)}
                                                        </div>
                                                        <div className="text-sm text-gray-500">
                                                            {incident.descripcion}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {incident.ubicacion}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {formatDate(incident.fecha_hora_inicio)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getSeverityColor(incident.severidad)}`}>
                                                    {incident.severidad?.charAt(0).toUpperCase() + incident.severidad?.slice(1)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getStatusColor(incident.estado)}`}>
                                                    {incident.estado?.replace('_', ' ').charAt(0).toUpperCase() + incident.estado?.slice(1).replace('_', ' ')}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() => handleViewIncident(incident.id)}
                                                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                                                    >
                                                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                        </svg>
                                                        Ver
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="7" className="px-6 py-12 text-center">
                                            <div className="text-gray-500">
                                                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                </svg>
                                                <h3 className="text-lg font-medium text-gray-900 mb-2">No hay incidentes</h3>
                                                <p className="text-gray-500">No se encontraron incidentes que coincidan con los filtros seleccionados.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Paginación */}
                    {totalPages > 1 && (
                        <div className="bg-white px-6 py-3 border-t border-gray-200 flex items-center justify-between">
                            <div className="text-sm text-gray-700">
                                Mostrando {indexOfFirstItem + 1} a {Math.min(indexOfLastItem, filteredIncidents.length)} de {filteredIncidents.length} incidentes
                            </div>
                            <div className="flex items-center space-x-2">
                                <button
                                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                    disabled={currentPage === 1}
                                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Anterior
                                </button>
                                
                                {[...Array(totalPages)].map((_, index) => (
                                    <button
                                        key={index + 1}
                                        onClick={() => setCurrentPage(index + 1)}
                                        className={`px-3 py-1 border rounded-md text-sm ${
                                            currentPage === index + 1
                                                ? 'bg-red-600 text-white border-red-600'
                                                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                                        }`}
                                    >
                                        {index + 1}
                                    </button>
                                ))}
                                
                                <button
                                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                    disabled={currentPage === totalPages}
                                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Siguiente
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Incidents;