import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const login = async (formData) => {
    try {
        const response = await axios.post(
            `${API_URL}/api/v1/auth/login`,
            formData,
            {
                headers: {
                    'Accept': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al iniciar sesión';
        throw new Error(message);
    }
};

export const getIncidents = async (params = {}) => {
    try {
        const response = await api.get('/api/v1/incidents', { params });
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener incidentes';
        throw new Error(message);
    }
};

// Nueva función para obtener un incidente específico
export const getIncident = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/incidents/${incidentId}`);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener el incidente';
        throw new Error(message);
    }
};

// Nueva función para actualizar un incidente
export const updateIncident = async (incidentId, updateData) => {
    try {
        const response = await api.patch(`/api/v1/incidents/${incidentId}`, updateData);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al actualizar el incidente';
        throw new Error(message);
    }
};

// Nueva función para obtener el video de evidencia
export const getIncidentVideo = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/incidents/${incidentId}/video`);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener el video de evidencia';
        throw new Error(message);
    }
};

export const getIncidentStats = async (fechaInicio, fechaFin) => {
    try {
        const response = await api.get('/api/v1/incidents/estadisticas', {
            params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin }
        });
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener estadísticas de incidentes';
        throw new Error(message);
    }
};

export const getCameras = async (activasSolo = false) => {
    try {
        const response = await api.get('/api/v1/cameras', {
            params: { activas_solo: activasSolo }
        });
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener cámaras';
        throw new Error(message);
    }
};

// Nueva función para obtener información del video
export const getVideoInfo = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/files/videos/${incidentId}/info`);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener información del video';
        throw new Error(message);
    }
};

// Nueva función para descargar video
export const downloadVideo = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/files/videos/${incidentId}`, {
            responseType: 'blob'
        });
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al descargar el video';
        throw new Error(message);
    }
};

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;