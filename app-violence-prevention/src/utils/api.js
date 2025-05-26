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