import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Reports = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    React.useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
        }
    }, [isAuthenticated, navigate]);

    return (
        <div className="py-6">
            <h1 className="text-2xl font-bold text-primary mb-4">Informes</h1>
            <p className="text-gray-600">
                Aquí podrás generar y visualizar informes. Esta sección se desarrollará en la próxima fase.
            </p>
        </div>
    );
};

export default Reports;