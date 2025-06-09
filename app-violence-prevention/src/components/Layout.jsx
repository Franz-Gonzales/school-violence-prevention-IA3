import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuth();
    
    // Estados para animaciones y interacciones
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [hoveredItem, setHoveredItem] = useState(null);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [fadeIn, setFadeIn] = useState(false);
    const [currentTime, setCurrentTime] = useState(new Date());

    // Activar animación al cargar y reloj
    useEffect(() => {
        setTimeout(() => setFadeIn(true), 100);
        
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        
        return () => clearInterval(timer);
    }, []);

    const menuItems = [
        { 
            name: 'Dashboard', 
            path: '/dashboard',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v14H8V5z" />
                </svg>
            ),
            gradient: 'from-blue-400 to-blue-500',
            color: 'text-blue-600',
            bgLight: 'bg-blue-50 border-blue-200'
        },
        { 
            name: 'Cámaras', 
            path: '/cameras',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
            ),
            gradient: 'from-green-400 to-green-500',
            color: 'text-green-600',
            bgLight: 'bg-green-50 border-green-200'
        },
        { 
            name: 'Incidentes', 
            path: '/incidents',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
            ),
            gradient: 'from-red-400 to-red-500',
            color: 'text-red-600',
            bgLight: 'bg-red-50 border-red-200'
        },
        { 
            name: 'Informes', 
            path: '/reports',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            ),
            gradient: 'from-purple-400 to-purple-500',
            color: 'text-purple-600',
            bgLight: 'bg-purple-50 border-purple-200'
        },
        { 
            name: 'Documentación', 
            path: '/documents',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            ),
            gradient: 'from-indigo-400 to-indigo-500',
            color: 'text-indigo-600',
            bgLight: 'bg-indigo-50 border-indigo-200'
        },
        { 
            name: 'Configuración', 
            path: '/settings',
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            ),
            gradient: 'from-gray-400 to-gray-500',
            color: 'text-gray-600',
            bgLight: 'bg-gray-50 border-gray-200'
        }
    ];

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const isActiveRoute = (path) => {
        return location.pathname === path || location.pathname.startsWith(path + '/');
    };

    return (
        <div className={`flex min-h-screen transition-opacity duration-1000 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
            {/* Barra Lateral Tema Claro */}
            <aside className={`bg-white shadow-xl border-r border-gray-200/50 transition-all duration-300 ease-in-out ${
                isCollapsed ? 'w-20' : 'w-72'
            } relative z-10`}>
                
                {/* Header del Sidebar */}
                <div className="relative">
                    {/* Background Pattern Sutil */}
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-50/30 to-red-50/30"></div>
                    
                    <div className={`relative p-6 border-b border-gray-200/70 ${isCollapsed ? 'px-4' : 'px-6'}`}>
                        <div className="flex items-center justify-between">
                            <div className={`flex items-center space-x-3 ${isCollapsed ? 'justify-center' : ''}`}>
                                {/* Logo/Icon */}
                                <div className="p-2 bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg transform hover:scale-110 transition-all duration-200">
                                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                    </svg>
                                </div>
                                
                                {/* Título */}
                                {!isCollapsed && (
                                    <div className="overflow-hidden">
                                        <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                                            SegurEscolar
                                        </h1>
                                        <p className="text-xs text-gray-500 mt-1">Sistema de Seguridad</p>
                                    </div>
                                )}
                            </div>
                            
                            {/* Toggle Button */}
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-all duration-200 transform hover:scale-110"
                            >
                                <svg className={`w-5 h-5 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Navigation Menu */}
                <nav className="flex-1 py-6 space-y-2 px-4">
                    {menuItems.map((item, index) => {
                        const isActive = isActiveRoute(item.path);
                        
                        return (
                            <div
                                key={item.name}
                                className="relative"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                {/* Active Indicator */}
                                {isActive && (
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-red-400 to-red-600 rounded-r-full"></div>
                                )}
                                
                                <button
                                    onClick={() => navigate(item.path)}
                                    onMouseEnter={() => setHoveredItem(item.name)}
                                    onMouseLeave={() => setHoveredItem(null)}
                                    className={`w-full flex items-center space-x-4 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                                        isActive 
                                            ? `bg-gradient-to-r ${item.gradient} text-white shadow-lg transform scale-105` 
                                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                                    } ${
                                        isCollapsed ? 'justify-center px-2' : ''
                                    }`}
                                >
                                    {/* Background Animation */}
                                    <div className={`absolute inset-0 bg-gradient-to-r ${item.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
                                    
                                    {/* Icon Container */}
                                    <div className={`relative z-10 p-1 rounded-lg transition-all duration-300 ${
                                        isActive 
                                            ? 'bg-white/20 shadow-lg' 
                                            : hoveredItem === item.name ? `${item.bgLight} shadow-sm` : ''
                                    }`}>
                                        <div className={`transition-all duration-300 transform ${
                                            hoveredItem === item.name ? 'scale-110 rotate-3' : ''
                                        } ${isActive ? 'text-white' : item.color}`}>
                                            {item.icon}
                                        </div>
                                    </div>
                                    
                                    {/* Menu Text */}
                                    {!isCollapsed && (
                                        <div className="relative z-10 flex-1 text-left">
                                            <span className={`font-medium transition-all duration-300 ${
                                                isActive ? 'font-bold text-white' : 'group-hover:font-semibold'
                                            }`}>
                                                {item.name}
                                            </span>
                                            
                                            {/* Subtitle for active items */}
                                            {isActive && (
                                                <div className="text-xs text-white/90 mt-1">
                                                    {item.name === 'Dashboard' && 'Panel Principal'}
                                                    {item.name === 'Cámaras' && 'Monitoreo en Vivo'}
                                                    {item.name === 'Incidentes' && 'Registro de Eventos'}
                                                    {item.name === 'Informes' && 'Análisis y Reportes'}
                                                    {item.name === 'Documentación' && 'Guías y Manuales'}
                                                    {item.name === 'Configuración' && 'Ajustes del Sistema'}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    
                                    {/* Arrow for active item */}
                                    {isActive && !isCollapsed && (
                                        <div className="relative z-10">
                                            <svg className="w-5 h-5 text-white/80 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    )}
                                </button>
                                
                                {/* Tooltip for collapsed state */}
                                {isCollapsed && hoveredItem === item.name && (
                                    <div className="absolute left-20 top-1/2 transform -translate-y-1/2 z-50">
                                        <div className="bg-gray-900 text-white px-3 py-2 rounded-lg shadow-xl whitespace-nowrap">
                                            <div className="font-medium">{item.name}</div>
                                            <div className="absolute left-0 top-1/2 transform -translate-x-1 -translate-y-1/2">
                                                <div className="w-2 h-2 bg-gray-900 transform rotate-45"></div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </nav>

                {/* User Profile Section */}
                <div className="border-t border-gray-200/70 p-4">
                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className={`w-full flex items-center space-x-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-all duration-300 group border border-gray-200/50 hover:border-gray-300/70 ${
                                isCollapsed ? 'justify-center' : ''
                            }`}
                        >
                            {/* Avatar */}
                            <div className="relative">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                                    {user?.nombre?.charAt(0)?.toUpperCase() || 'U'}
                                </div>
                                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
                            </div>
                            
                            {!isCollapsed && (
                                <div className="flex-1 text-left">
                                    <div className="text-gray-900 font-medium">{user?.nombre || 'Usuario'}</div>
                                    <div className="text-gray-500 text-xs capitalize">{user?.rol || 'Rol'}</div>
                                </div>
                            )}
                            
                            {!isCollapsed && (
                                <svg className={`w-5 h-5 text-gray-500 transition-transform duration-300 ${showUserMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            )}
                        </button>
                        
                        {/* User Menu Dropdown */}
                        {showUserMenu && (
                            <div className={`absolute bottom-full left-0 right-0 mb-2 bg-white rounded-xl border border-gray-200 shadow-xl overflow-hidden transform transition-all duration-300 ${
                                isCollapsed ? 'left-20 right-auto w-48' : ''
                            }`}>
                                <button className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-50 transition-colors text-gray-700 hover:text-gray-900">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                    </svg>
                                    <span>Mi Perfil</span>
                                </button>
                                
                                <button className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-50 transition-colors text-gray-700 hover:text-gray-900">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM19 12H5l7-7 7 7z" />
                                    </svg>
                                    <span>Notificaciones</span>
                                </button>
                                
                                <div className="border-t border-gray-200">
                                    <button
                                        onClick={handleLogout}
                                        className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-red-50 transition-colors text-red-600 hover:text-red-700"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                        </svg>
                                        <span>Cerrar Sesión</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Contenido Principal */}
            <main className={`flex-1 min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 transition-all duration-300`}>
                {/* Top Bar Rediseñada */}
                <div className="bg-white/90 backdrop-blur-sm border-b border-gray-200/60 shadow-sm">
                    <div className="px-6 py-4">
                        <div className="flex items-center justify-between">
                            {/* Breadcrumb */}
                            <div className="flex items-center space-x-2 text-sm">
                                <div className="flex items-center space-x-2 text-gray-500">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                                    </svg>
                                    <span>SegurEscolar</span>
                                </div>
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                <span className="text-gray-900 font-medium capitalize">
                                    {location.pathname.split('/')[1] || 'Dashboard'}
                                </span>
                            </div>
                            
                            {/* Status Indicators */}
                            <div className="flex items-center space-x-6">
                                <div className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                    <span className="text-sm text-gray-600">Sistema Operativo</span>
                                </div>
                                
                                {/* Real time clock */}
                                <div className="flex items-center space-x-2">
                                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <div className="text-sm text-gray-600 font-mono">
                                        {currentTime.toLocaleTimeString('es-ES')}
                                    </div>
                                </div>
                                
                                {/* Quick actions */}
                                <div className="flex items-center space-x-2">
                                    <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM19 12H5l7-7 7 7z" />
                                        </svg>
                                    </button>
                                    <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Main Content */}
                <div className="p-6">
                    {children}
                </div>
            </main>

            {/* Overlay for mobile */}
            {!isCollapsed && (
                <div 
                    className="fixed inset-0 bg-black/20 z-0 lg:hidden"
                    onClick={() => setIsCollapsed(true)}
                />
            )}
        </div>
    );
};

export default Layout;