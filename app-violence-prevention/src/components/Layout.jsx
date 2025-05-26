import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuth();

    const menuItems = [
        { name: 'Dashboard', path: '/dashboard' },
        { name: 'Cámaras', path: '/cameras' },
        { name: 'Incidentes', path: '/incidents' },
        { name: 'Informes', path: '/reports' },
        { name: 'Documentación', path: '/documents' },
        { name: 'Configuración', path: '/settings' },
    ];

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="flex">
            {/* Barra Lateral */}
            <aside className="sidebar">
                <div className="p-4">
                    <h1 className="text-2xl font-bold text-primary">SegurEscolar</h1>
                </div>
                <nav className="mt-6">
                    {menuItems.map((item) => (
                        <div
                            key={item.name}
                            onClick={() => navigate(item.path)}
                            className={`sidebar-item cursor-pointer ${
                                location.pathname === item.path ? 'active' : ''
                            }`}
                        >
                            <span>{item.name}</span>
                        </div>
                    ))}
                </nav>
                <div className="absolute bottom-4 px-4 w-64">
                    <div className="border-t pt-4">
                        <p className="text-gray-600">
                            {user?.nombre} ({user?.rol})
                        </p>
                        <button
                            onClick={handleLogout}
                            className="mt-2 w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </aside>

            {/* Contenido Principal */}
            <main className="main-content flex-1 min-h-screen bg-background">
                {children}
            </main>
        </div>
    );
};

export default Layout;