import React, { useState, useEffect } from 'react';
import { login } from '../utils/api';

const Auth = ({ onLogin }) => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [focusedField, setFocusedField] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    // Animación de entrada
    useEffect(() => {
        setTimeout(() => setShowForm(true), 300);
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Limpiar error cuando el usuario empieza a escribir
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.username || !formData.password) {
            setError('Por favor, completa todos los campos');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const formBody = new FormData();
            formBody.append('username', formData.username);
            formBody.append('password', formData.password);

            const data = await login(formBody);
            onLogin(data);
        } catch (err) {
            setError(err.message || 'Error al iniciar sesión');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50 flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-5">
                <div className="absolute top-20 left-20 w-32 h-32 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="absolute top-40 right-32 w-24 h-24 bg-red-500 rounded-full animate-pulse delay-1000"></div>
                <div className="absolute bottom-32 left-1/3 w-20 h-20 bg-green-500 rounded-full animate-pulse delay-2000"></div>
                <div className="absolute bottom-20 right-20 w-28 h-28 bg-purple-500 rounded-full animate-pulse delay-3000"></div>
            </div>

            {/* Floating Elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {[...Array(6)].map((_, i) => (
                    <div
                        key={i}
                        className={`absolute animate-float-${i % 3 + 1} opacity-10`}
                        style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                            animationDelay: `${i * 2}s`
                        }}
                    >
                        <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                    </div>
                ))}
            </div>

            {/* Main Login Card */}
            <div className={`max-w-md w-full transform transition-all duration-1000 ${
                showForm ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
            }`}>
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
                    {/* Header Section */}
                    <div className="relative bg-gradient-to-r from-blue-600 via-blue-700 to-red-600 p-8 text-center">
                        {/* Decorative Elements */}
                        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/10 to-transparent"></div>
                        <div className="absolute -top-4 -right-4 w-24 h-24 bg-white/10 rounded-full animate-pulse"></div>
                        <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-white/5 rounded-full animate-pulse delay-1000"></div>
                        
                        {/* Logo/Icon */}
                        <div className="relative z-10 mb-4">
                            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 rounded-2xl shadow-lg backdrop-blur-sm transform hover:scale-110 transition-all duration-300 group">
                                <svg className="w-12 h-12 text-white group-hover:animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                        </div>

                        {/* Title */}
                        <div className="relative z-10">
                            <h1 className="text-3xl font-bold text-white mb-2 animate-fade-in">
                                SegurEscolar
                            </h1>
                            <p className="text-blue-100 text-sm font-medium animate-fade-in delay-500">
                                Sistema de Seguridad Educativa
                            </p>
                            <div className="mt-3 text-xs text-blue-200 animate-fade-in delay-1000">
                                🛡️ Protegiendo nuestro entorno educativo
                            </div>
                        </div>

                        {/* Decorative Wave */}
                        <div className="absolute bottom-0 left-0 w-full">
                            <svg className="w-full h-6 text-white" fill="currentColor" viewBox="0 0 1200 120" preserveAspectRatio="none">
                                <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"/>
                            </svg>
                        </div>
                    </div>

                    {/* Form Section */}
                    <div className="p-8">
                        <div className="text-center mb-8">
                            <h2 className="text-xl font-semibold text-gray-800 mb-2">
                                Acceso al Sistema
                            </h2>
                            <p className="text-gray-600 text-sm">
                                Ingresa tus credenciales para continuar
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            {/* Username Field */}
                            <div className="relative">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    👤 Usuario
                                </label>
                                <div className="relative">
                                    <input
                                        id="username"
                                        name="username"
                                        type="text"
                                        value={formData.username}
                                        onChange={handleChange}
                                        onFocus={() => setFocusedField('username')}
                                        onBlur={() => setFocusedField('')}
                                        className={`w-full px-4 py-3 pl-12 border-2 rounded-xl shadow-sm transition-all duration-300 bg-white/70 backdrop-blur-sm focus:outline-none ${
                                            focusedField === 'username'
                                                ? 'border-blue-500 ring-4 ring-blue-500/20 transform scale-[1.02]'
                                                : 'border-gray-300 hover:border-gray-400'
                                        } ${error && !formData.username ? 'border-red-400' : ''}`}
                                        placeholder="Nombre de usuario"
                                        required
                                    />
                                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            {/* Password Field */}
                            <div className="relative">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    🔒 Contraseña
                                </label>
                                <div className="relative">
                                    <input
                                        id="password"
                                        name="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={formData.password}
                                        onChange={handleChange}
                                        onFocus={() => setFocusedField('password')}
                                        onBlur={() => setFocusedField('')}
                                        className={`w-full px-4 py-3 pl-12 pr-12 border-2 rounded-xl shadow-sm transition-all duration-300 bg-white/70 backdrop-blur-sm focus:outline-none ${
                                            focusedField === 'password'
                                                ? 'border-blue-500 ring-4 ring-blue-500/20 transform scale-[1.02]'
                                                : 'border-gray-300 hover:border-gray-400'
                                        } ${error && !formData.password ? 'border-red-400' : ''}`}
                                        placeholder="Tu contraseña"
                                        required
                                    />
                                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                        </svg>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        {showPassword ? (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                                            </svg>
                                        ) : (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-lg animate-shake">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0">
                                            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                            </svg>
                                        </div>
                                        <div className="ml-3">
                                            <p className="text-sm text-red-700 font-medium">
                                                {error}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={loading}
                                className={`w-full relative overflow-hidden bg-gradient-to-r from-blue-600 to-red-600 hover:from-blue-700 hover:to-red-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-blue-500/30 ${
                                    loading ? 'opacity-70 cursor-not-allowed' : 'hover:shadow-2xl'
                                }`}
                            >
                                {/* Button Background Animation */}
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                                
                                <div className="relative flex items-center justify-center space-x-2">
                                    {loading ? (
                                        <>
                                            <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            <span>Verificando credenciales...</span>
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                                            </svg>
                                            <span>Iniciar Sesión</span>
                                        </>
                                    )}
                                </div>
                            </button>
                        </form>

                        {/* Footer */}
                        <div className="mt-8 text-center">
                            <div className="text-xs text-gray-500 space-y-1">
                                <p>🏫 Plataforma de Seguridad Educativa</p>
                                <p>🔒 Acceso restringido solo para personal autorizado</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Security Notice */}
                <div className="mt-6 text-center">
                    <div className="inline-flex items-center space-x-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-lg border border-white/30">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-gray-600 font-medium">Conexión segura</span>
                        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Auth;