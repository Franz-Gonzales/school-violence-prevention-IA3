import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
    const navigate = useNavigate();
    const { user, logout, isAuthenticated } = useAuth();

    React.useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
        }
    }, [isAuthenticated, navigate]);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    if (!user) {
        return null;
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-primary">Dashboard</h1>
                <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                    Cerrar Sesión
                </button>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
                <h2 className="text-xl mb-4">Bienvenido, {user.nombre}</h2>
                <p>Rol: {user.rol}</p>
            </div>
        </div>
    );
};

export default Dashboard;