import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, validateSession, isLoading } = useAuth();
    const [isValidating, setIsValidating] = useState(true);
    const [isValid, setIsValid] = useState(false);
    const location = useLocation();

    useEffect(() => {
        const checkSession = async () => {
            if (!isAuthenticated) {
                setIsValidating(false);
                setIsValid(false);
                return;
            }

            try {
                const valid = await validateSession();
                setIsValid(valid);
            } catch (error) {
                console.error('Error validating session:', error);
                setIsValid(false);
            } finally {
                setIsValidating(false);
            }
        };

        checkSession();
    }, [isAuthenticated, validateSession, location.pathname]);

    if (isLoading || isValidating) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Verificando sesión...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated || !isValid) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;