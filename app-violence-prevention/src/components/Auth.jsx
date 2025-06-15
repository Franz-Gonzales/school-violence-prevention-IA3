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
        if (error) { setError(''); }
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
        <div className="min-h-screen bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100 flex items-center justify-center p-2 sm:p-4 relative overflow-hidden">
            {/* Desktop Background Pattern */}
            <div className="absolute inset-0">
                {/* Grid pattern for desktop feel */}
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-400/5 via-indigo-500/5 to-purple-600/5"></div>
                <div 
                    className="absolute inset-0 opacity-20"
                    style={{
                        backgroundImage: `
                            linear-gradient(45deg, transparent 45%, rgba(59, 130, 246, 0.1) 49%, rgba(59, 130, 246, 0.1) 51%, transparent 55%),
                            linear-gradient(-45deg, transparent 45%, rgba(99, 102, 241, 0.1) 49%, rgba(99, 102, 241, 0.1) 51%, transparent 55%)
                        `,
                        backgroundSize: '60px 60px'
                    }}
                ></div>
                
                {/* Floating geometric elements */}
                <div className="absolute top-1/4 left-1/4 w-24 h-24 border-2 border-blue-300/30 rounded-lg rotate-12 animate-pulse"></div>
                <div className="absolute top-1/3 right-1/4 w-20 h-20 bg-gradient-to-br from-indigo-400/20 to-purple-500/20 rounded-xl rotate-45 animate-bounce" style={{animationDuration: '3s'}}></div>
                <div className="absolute bottom-1/4 left-1/3 w-24 h-24 border-2 border-purple-300/30 rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                <div className="absolute bottom-1/3 right-1/3 w-16 h-16 bg-gradient-to-br from-blue-400/20 to-cyan-500/20 rounded-lg rotate-12 animate-bounce" style={{animationDuration: '4s', animationDelay: '2s'}}></div>
            </div>

            {/* Main Desktop Login Container - TAMAÑO OPTIMIZADO */}
            <div className={`w-full max-w-7xl xl:max-w-[88vw] grid lg:grid-cols-5 gap-4 lg:gap-6 xl:gap-8 transform transition-all duration-1000 ${
                showForm ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
            }`}>
                
                {/* Left Panel - Branding & Information (Hidden on mobile) - TAMAÑO REDUCIDO */}
                <div className="hidden lg:flex lg:col-span-3 bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 rounded-2xl lg:rounded-3xl shadow-2xl p-6 lg:p-8 xl:p-12 text-white relative overflow-hidden min-h-[580px] lg:min-h-[600px] xl:min-h-[650px]">
                    {/* Background decorations */}
                    <div className="absolute inset-0">
                        <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full -translate-y-24 translate-x-24"></div>
                        <div className="absolute bottom-0 left-0 w-40 h-40 bg-white/5 rounded-full translate-y-20 -translate-x-20"></div>
                        <div className="absolute top-1/2 left-1/2 w-24 h-24 bg-gradient-to-br from-cyan-400/20 to-blue-500/20 rounded-lg rotate-45 -translate-x-1/2 -translate-y-1/2"></div>
                    </div>

                    <div className="relative z-10 flex flex-col justify-between h-full w-full">
                        {/* Header Section */}
                        <div>
                            <div className="flex items-center space-x-3 lg:space-x-4 mb-6 lg:mb-8">
                                <div className="w-14 h-14 lg:w-16 lg:h-16 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-xl lg:rounded-2xl flex items-center justify-center shadow-xl">
                                    <svg className="w-8 h-8 lg:w-10 lg:h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                    </svg>
                                </div>
                                <div>
                                    <h1 className="text-3xl lg:text-4xl xl:text-5xl font-bold">SegurEscolar</h1>
                                    <p className="text-blue-200 text-base lg:text-lg xl:text-xl">Sistema de Seguridad Educativa</p>
                                </div>
                            </div>

                            <div className="space-y-4 lg:space-y-6 mb-8 lg:mb-10">
                                <h2 className="text-2xl lg:text-3xl xl:text-4xl font-bold leading-tight">
                                    Protección Inteligente para<br />
                                    <span className="text-cyan-300">Centros Educativos</span>
                                </h2>
                                <p className="text-blue-100 text-base lg:text-lg xl:text-xl leading-relaxed">
                                    Tecnología de vanguardia con inteligencia artificial para garantizar 
                                    un ambiente de aprendizaje seguro y protegido las 24 horas del día.
                                </p>
                            </div>

                            {/* Features Grid - COMPACTO */}
                            <div className="grid grid-cols-2 gap-4 lg:gap-6">
                                <div className="bg-white/10 backdrop-blur-sm rounded-xl lg:rounded-2xl p-4 lg:p-6 border border-white/20">
                                    <div className="flex items-center space-x-2 lg:space-x-3 mb-2 lg:mb-3">
                                        <div className="w-8 h-8 lg:w-10 lg:h-10 bg-green-400/20 rounded-lg flex items-center justify-center">
                                            <span className="text-green-300 text-lg lg:text-xl">🤖</span>
                                        </div>
                                        <h3 className="font-semibold text-sm lg:text-base xl:text-lg">Detección IA</h3>
                                    </div>
                                    <p className="text-blue-100 text-xs lg:text-sm">
                                        Algoritmos avanzados de machine learning para identificación automática de situaciones de riesgo
                                    </p>
                                </div>

                                <div className="bg-white/10 backdrop-blur-sm rounded-xl lg:rounded-2xl p-4 lg:p-6 border border-white/20">
                                    <div className="flex items-center space-x-2 lg:space-x-3 mb-2 lg:mb-3">
                                        <div className="w-8 h-8 lg:w-10 lg:h-10 bg-yellow-400/20 rounded-lg flex items-center justify-center">
                                            <span className="text-yellow-300 text-lg lg:text-xl">⚡</span>
                                        </div>
                                        <h3 className="font-semibold text-sm lg:text-base xl:text-lg">Respuesta Rápida</h3>
                                    </div>
                                    <p className="text-blue-100 text-xs lg:text-sm">
                                        Alertas instantáneas y protocolos automatizados para una respuesta inmediata ante incidentes
                                    </p>
                                </div>

                                <div className="bg-white/10 backdrop-blur-sm rounded-xl lg:rounded-2xl p-4 lg:p-6 border border-white/20">
                                    <div className="flex items-center space-x-2 lg:space-x-3 mb-2 lg:mb-3">
                                        <div className="w-8 h-8 lg:w-10 lg:h-10 bg-purple-400/20 rounded-lg flex items-center justify-center">
                                            <span className="text-purple-300 text-lg lg:text-xl">📊</span>
                                        </div>
                                        <h3 className="font-semibold text-sm lg:text-base xl:text-lg">Monitoreo 24/7</h3>
                                    </div>
                                    <p className="text-blue-100 text-xs lg:text-sm">
                                        Vigilancia continua con análisis en tiempo real de todas las áreas del centro educativo
                                    </p>
                                </div>

                                <div className="bg-white/10 backdrop-blur-sm rounded-xl lg:rounded-2xl p-4 lg:p-6 border border-white/20">
                                    <div className="flex items-center space-x-2 lg:space-x-3 mb-2 lg:mb-3">
                                        <div className="w-8 h-8 lg:w-10 lg:h-10 bg-red-400/20 rounded-lg flex items-center justify-center">
                                            <span className="text-red-300 text-lg lg:text-xl">🔒</span>
                                        </div>
                                        <h3 className="font-semibold text-sm lg:text-base xl:text-lg">Máxima Seguridad</h3>
                                    </div>
                                    <p className="text-blue-100 text-xs lg:text-sm">
                                        Cifrado de extremo a extremo y protocolos de seguridad enterprise para proteger toda la información
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Footer Stats - COMPACTO */}
                        <div className="border-t border-white/20 pt-4 lg:pt-6">
                            <div className="grid grid-cols-3 gap-4 lg:gap-6 text-center">
                                <div>
                                    <div className="text-xl lg:text-2xl xl:text-3xl font-bold text-cyan-300">99.9%</div>
                                    <div className="text-blue-200 text-xs lg:text-sm">Precisión IA</div>
                                </div>
                                <div>
                                    <div className="text-xl lg:text-2xl xl:text-3xl font-bold text-green-300">&lt;1s</div>
                                    <div className="text-blue-200 text-xs lg:text-sm">Tiempo Respuesta</div>
                                </div>
                                <div>
                                    <div className="text-xl lg:text-2xl xl:text-3xl font-bold text-yellow-300">24/7</div>
                                    <div className="text-blue-200 text-xs lg:text-sm">Operación</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel - Login Form - TAMAÑO OPTIMIZADO */}
                <div className="lg:col-span-2 w-full">
                    {/* Mobile Header (Visible only on mobile) */}
                    <div className="lg:hidden bg-white/95 backdrop-blur-lg rounded-t-2xl shadow-xl border border-white/20 p-4 mb-0">
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl shadow-lg mb-3">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                            <h1 className="text-xl font-bold text-gray-800 mb-1">SegurEscolar</h1>
                            <p className="text-blue-600 font-medium text-sm">Sistema de Seguridad Educativa</p>
                        </div>
                    </div>

                    {/* Login Form Container - TAMAÑO REDUCIDO */}
                    <div className="bg-white/95 backdrop-blur-lg lg:rounded-2xl lg:rounded-t-3xl rounded-b-2xl shadow-2xl border border-white/20 p-5 sm:p-6 lg:p-8 xl:p-10 min-h-[580px] lg:min-h-[600px] xl:min-h-[650px] flex flex-col justify-center">
                        
                        {/* Desktop Welcome Message */}
                        <div className="text-center mb-6 lg:mb-8">
                            <div className="hidden lg:block mb-4 lg:mb-6">
                                <div className="inline-flex items-center justify-center w-16 h-16 lg:w-20 lg:h-20 xl:w-24 xl:h-24 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl lg:rounded-3xl shadow-xl mb-3 lg:mb-4">
                                    <svg className="w-8 h-8 lg:w-10 lg:h-10 xl:w-12 xl:h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                                    </svg>
                                </div>
                            </div>
                            <h2 className="text-2xl lg:text-3xl xl:text-4xl font-bold text-gray-800 mb-2 lg:mb-3">
                                Panel de Control
                            </h2>
                            <p className="text-gray-600 text-sm lg:text-base xl:text-lg">
                                Accede con tus credenciales autorizadas
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5 lg:space-y-6 xl:space-y-7">
                            {/* Username Field */}
                            <div className="space-y-2">
                                <label className="text-sm lg:text-base font-semibold text-gray-700 flex items-center space-x-2">
                                    <span className="text-blue-500 text-base lg:text-lg">👤</span>
                                    <span>Usuario del Sistema</span>
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
                                        className={`w-full px-4 lg:px-5 xl:px-6 py-3 lg:py-4 xl:py-4 pl-11 lg:pl-12 xl:pl-14 border-2 rounded-xl shadow-sm transition-all duration-300 bg-white/80 backdrop-blur-sm focus:outline-none font-medium text-base lg:text-lg ${
                                            focusedField === 'username'
                                                ? 'border-blue-500 ring-4 ring-blue-500/20 transform scale-[1.01] shadow-lg'
                                                : 'border-gray-300 hover:border-gray-400'
                                        } ${error && !formData.username ? 'border-red-400 ring-4 ring-red-400/20' : ''}`}
                                        placeholder="Nombre de usuario"
                                        required
                                    />
                                    <div className="absolute left-4 lg:left-5 xl:left-6 top-1/2 transform -translate-y-1/2 text-gray-400">
                                        <svg className="w-5 h-5 lg:w-5 lg:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            {/* Password Field */}
                            <div className="space-y-2">
                                <label className="text-sm lg:text-base font-semibold text-gray-700 flex items-center space-x-2">
                                    <span className="text-green-500 text-base lg:text-lg">🔐</span>
                                    <span>Contraseña de Acceso</span>
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
                                        className={`w-full px-4 lg:px-5 xl:px-6 py-3 lg:py-4 xl:py-4 pl-11 lg:pl-12 xl:pl-14 pr-11 lg:pr-12 xl:pr-14 border-2 rounded-xl shadow-sm transition-all duration-300 bg-white/80 backdrop-blur-sm focus:outline-none font-medium text-base lg:text-lg ${
                                            focusedField === 'password'
                                                ? 'border-blue-500 ring-4 ring-blue-500/20 transform scale-[1.01] shadow-lg'
                                                : 'border-gray-300 hover:border-gray-400'
                                        } ${error && !formData.password ? 'border-red-400 ring-4 ring-red-400/20' : ''}`}
                                        placeholder="Contraseña"
                                        required
                                    />
                                    <div className="absolute left-4 lg:left-5 xl:left-6 top-1/2 transform -translate-y-1/2 text-gray-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                        </svg>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 lg:right-5 xl:right-6 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
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
                                <div className="bg-red-50 border border-red-200 rounded-xl p-4 animate-pulse">
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
                                className={`w-full relative overflow-hidden bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:via-blue-800 hover:to-indigo-800 text-white font-bold py-3 lg:py-4 xl:py-5 px-6 rounded-xl shadow-xl transition-all duration-300 transform hover:scale-[1.02] hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/30 text-base lg:text-lg xl:text-xl ${
                                    loading ? 'opacity-70 cursor-not-allowed' : ''
                                }`}
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 transform -skew-x-12 -translate-x-full hover:translate-x-full transition-transform duration-1000"></div>
                                
                                <div className="relative flex items-center justify-center space-x-3">
                                    {loading ? (
                                        <>
                                            <svg className="animate-spin h-5 w-5 lg:h-6 lg:w-6 text-white" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            <span>Verificando credenciales...</span>
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-5 h-5 lg:w-6 lg:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                                            </svg>
                                            <span>Acceder al Sistema</span>
                                        </>
                                    )}
                                </div>
                            </button>
                        </form>

                        {/* Security Features Footer */}
                        <div className="mt-6 lg:mt-8 pt-4 lg:pt-6 border-t border-gray-200">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:gap-4 text-center">
                                <div className="flex flex-col items-center space-y-1 lg:space-y-2">
                                    <div className="w-8 h-8 lg:w-10 lg:h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                        <span className="text-blue-600 text-sm lg:text-base">🔒</span>
                                    </div>
                                    <p className="text-xs lg:text-sm text-gray-600 font-medium">Cifrado SSL</p>
                                </div>
                                <div className="flex flex-col items-center space-y-1 lg:space-y-2">
                                    <div className="w-8 h-8 lg:w-10 lg:h-10 bg-green-100 rounded-full flex items-center justify-center">
                                        <span className="text-green-600 text-sm lg:text-base">🛡️</span>
                                    </div>
                                    <p className="text-xs lg:text-sm text-gray-600 font-medium">Protección IA</p>
                                </div>
                                <div className="flex flex-col items-center space-y-1 lg:space-y-2">
                                    <div className="w-8 h-8 lg:w-10 lg:h-10 bg-purple-100 rounded-full flex items-center justify-center">
                                        <span className="text-purple-600 text-sm lg:text-base">📊</span>
                                    </div>
                                    <p className="text-xs lg:text-sm text-gray-600 font-medium">Monitoreo 24/7</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Connection Status Badge */}
                    <div className="mt-4 lg:mt-6 text-center">
                        <div className="inline-flex items-center space-x-2 bg-white/90 backdrop-blur-sm px-3 lg:px-4 py-2 rounded-full shadow-lg border border-green-200">
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                <span className="text-sm text-gray-700 font-semibold">Sistema Operativo</span>
                            </div>
                            <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Auth;