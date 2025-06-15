import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('user');
        const token = localStorage.getItem('token');
        
        // Verificar si hay token y usuario guardados
        if (savedUser && token) {
            try {
                // Verificar si el token no ha expirado
                if (isTokenValid(token)) {
                    return JSON.parse(savedUser);
                } else {
                    // Token expirado, limpiar storage
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    console.log('🔒 Token expirado, sesión limpiada');
                }
            } catch (error) {
                console.error('Error al verificar token:', error);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
        return null;
    });

    const [isLoading, setIsLoading] = useState(false);

    // Verificar la validez del token
    const isTokenValid = (token) => {
        if (!token){ return false; }
        
        try {
            // Decodificar el payload del JWT (sin verificar la firma)
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            
            // Verificar si el token no ha expirado
            return payload.exp && payload.exp > currentTime;
        } catch (error) {
            console.error('Error al decodificar token:', error);
            return false;
        }
    };

    // Verificar token periódicamente
    useEffect(() => {
        const checkTokenValidity = () => {
            const token = localStorage.getItem('token');
            
            if (token && !isTokenValid(token)) {
                console.log('🔒 Token expirado, cerrando sesión automáticamente');
                logout();
            }
        };

        // Verificar cada 5 minutos
        const interval = setInterval(checkTokenValidity, 5 * 60 * 1000);
        
        // Verificar inmediatamente al cargar
        checkTokenValidity();

        return () => clearInterval(interval);
    }, []);

    // Verificar token antes de cada navegación
    const validateSession = useCallback(async () => {
        const token = localStorage.getItem('token');
        
        if (!token || !isTokenValid(token)) {
            await logout();
            return false;
        }

        try {
            // Verificar con el servidor que el token sigue siendo válido
            const response = await api.get('/api/v1/auth/perfil');
            
            if (response.status === 200) {
                return true;
            }
        } catch (error) {
            if (error.response?.status === 401) {
                console.log('🔒 Token inválido según servidor, cerrando sesión');
                await logout();
                return false;
            }
        }
        
        return true;
    }, []);

    const login = useCallback((userData) => {
        console.log('🔐 Iniciando sesión:', userData.usuario?.email);
        
        localStorage.setItem('token', userData.access_token);
        localStorage.setItem('user', JSON.stringify(userData.usuario));
        setUser(userData.usuario);
        
        // Configurar auto-logout antes de que expire el token
        const token = userData.access_token;
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const expirationTime = payload.exp * 1000; // Convertir a milliseconds
                const currentTime = Date.now();
                const timeUntilExpiry = expirationTime - currentTime;
                
                // Auto-logout 1 minuto antes de que expire
                const autoLogoutTime = Math.max(timeUntilExpiry - 60000, 10000);
                
                setTimeout(() => {
                    console.log('🔒 Token próximo a expirar, cerrando sesión automáticamente');
                    logout();
                }, autoLogoutTime);
                
                console.log(`⏰ Auto-logout programado en ${Math.round(autoLogoutTime / 1000)} segundos`);
            } catch (error) {
                console.error('Error configurando auto-logout:', error);
            }
        }
    }, []);

    const logout = useCallback(async () => {
        setIsLoading(true);
        
        try {
            // Intentar notificar al servidor del logout
            await api.post('/api/v1/auth/logout');
        } catch (error) {
            console.error('Error en logout del servidor:', error);
        } finally {
            // Limpiar estado local siempre
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            setIsLoading(false);
            
            console.log('🔓 Sesión cerrada correctamente');
            
            // Opcional: Recargar la página para limpiar cualquier estado residual
            window.location.href = '/login';
        }
    }, []);

    const refreshToken = useCallback(async () => {
        try {
            const response = await api.post('/api/v1/auth/refresh');
            const newTokenData = response.data;
            
            localStorage.setItem('token', newTokenData.access_token);
            console.log('🔄 Token renovado exitosamente');
            
            return true;
        } catch (error) {
            console.error('Error renovando token:', error);
            await logout();
            return false;
        }
    }, [logout]);

    return (
        <AuthContext.Provider value={{ 
            user, 
            login, 
            logout, 
            isLoading,
            isAuthenticated: !!user,
            validateSession,
            refreshToken,
            isTokenValid: () => {
                const token = localStorage.getItem('token');
                return isTokenValid(token);
            }
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth debe usarse dentro de AuthProvider');
    }
    return context;
};