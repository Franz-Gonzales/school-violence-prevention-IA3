import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Función para verificar si el token es válido
const isTokenValid = (token) => {
    if (!token){ return false;}
    
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        return payload.exp && payload.exp > currentTime;
    } catch (error) {
        return false;
    }
};

// Función para limpiar sesión
const clearSession = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
};

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

export const getIncident = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/incidents/${incidentId}`);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener el incidente';
        throw new Error(message);
    }
};

export const updateIncident = async (incidentId, updateData) => {
    try {
        const response = await api.patch(`/api/v1/incidents/${incidentId}`, updateData);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al actualizar el incidente';
        throw new Error(message);
    }
};

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
        
        console.log('📹 Cámaras obtenidas:', response.data);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener cámaras';
        console.error('Error obteniendo cámaras:', message);
        throw new Error(message);
    }
};

export const getVideoInfo = async (incidentId) => {
    try {
        const response = await api.get(`/api/v1/files/videos/${incidentId}/info`);
        return response.data;
    } catch (error) {
        const message = error.response?.data?.detail || 'Error al obtener información del video';
        throw new Error(message);
    }
};

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

// Instancia de Axios con interceptores mejorados
export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    timeout: 10000 // 10 segundos de timeout
});

// Interceptor de request - Verificar token antes de cada petición
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        
        if (token) {
            if (isTokenValid(token)) {
                config.headers.Authorization = `Bearer ${token}`;
            } else {
                console.log('🔒 Token expirado detectado en interceptor de request');
                clearSession();
                return Promise.reject(new Error('Token expirado'));
            }
        }
        
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Interceptor de response - Manejar errores de autenticación
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            console.log('🔒 Error 401 detectado, token inválido');
            
            // Intentar refrescar el token una sola vez
            try {
                const refreshResponse = await axios.post(`${API_URL}/api/v1/auth/refresh`, {}, {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('token')}`
                    }
                });
                
                const newToken = refreshResponse.data.access_token;
                localStorage.setItem('token', newToken);
                
                // Reintentar la request original con el nuevo token
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
                
            } catch (refreshError) {
                console.log('🔒 No se pudo refrescar el token, cerrando sesión');
                clearSession();
                return Promise.reject(refreshError);
            }
        }
        
        // Si es otro tipo de error 401 o ya se intentó refrescar
        if (error.response?.status === 401) {
            console.log('🔒 Credenciales inválidas, cerrando sesión');
            clearSession();
        }
        
        return Promise.reject(error);
    }
);

export default api;