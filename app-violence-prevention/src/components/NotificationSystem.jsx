import React, { useState, useEffect, useRef } from 'react';

// Componente de notificación individual
const NotificationItem = ({ notification, onClose, onAction }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [isClosing, setIsClosing] = useState(false);
    const [timeLeft, setTimeLeft] = useState(15); // Para mostrar countdown

    useEffect(() => {
        setIsVisible(true);

        // *** TIEMPOS ESPECÍFICOS PARA CADA TIPO ***
        let autoCloseTime;
        if (notification.type === 'violence') {
            autoCloseTime = 8000; // 8 segundos para violencia
        } else if (notification.type === 'error') {
            autoCloseTime = 10000; // 10 segundos para errores
        } else {
            autoCloseTime = 6000; // 6 segundos para otras
        }

        // *** COUNTDOWN TIMER (solo para violencia) ***
        let countdownInterval;
        if (notification.type === 'violence') {
            const startTime = Date.now();
            countdownInterval = setInterval(() => {
                const elapsed = Date.now() - startTime;
                const remaining = Math.max(0, Math.ceil((autoCloseTime - elapsed) / 1000));
                setTimeLeft(remaining);
                
                if (remaining <= 0) {
                    clearInterval(countdownInterval);
                }
            }, 100);
        }

        const timer = setTimeout(() => {
            handleClose();
        }, autoCloseTime);

        return () => {
            clearTimeout(timer);
            if (countdownInterval) {
                clearInterval(countdownInterval);
            }
        };
    }, []);

    const handleClose = () => {
        setIsClosing(true);
        setTimeout(() => {
            onClose(notification.id);
        }, 300);
    };

    // RESTO DEL COMPONENTE PERMANECE IGUAL, PERO AGREGAR countdown para violencia:
    
    return (
        <div className={`p-4 rounded-lg mb-3 ${getNotificationStyles()}`}>
            <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                    <div className="text-2xl">{getIcon()}</div>
                    <div className="flex-1">
                        <div className={`font-medium ${getTextColor()}`}>
                            {notification.title || notification.message}
                        </div>
                        {notification.details && (
                            <div className="text-sm text-gray-600 mt-1">
                                {notification.details}
                            </div>
                        )}
                        <div className="text-xs text-gray-500 mt-2 flex items-center justify-between">
                            <span>{notification.timestamp.toLocaleTimeString()}</span>
                            {/* *** NUEVO: Mostrar countdown para violencia *** */}
                            {notification.type === 'violence' && timeLeft > 0 && (
                                <span className="text-red-600 font-bold">
                                    Auto-cierre en {timeLeft}s
                                </span>
                            )}
                        </div>

                        {/* *** DATOS ESPECÍFICOS PARA ALERTAS DE VIOLENCIA CON VERIFICACIÓN MÚLTIPLE *** */}
                        {notification.type === 'violence' && notification.data && (
                            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="font-medium">Probabilidad:</span>
                                    <span className="ml-1 font-bold text-red-600">
                                        {(() => {
                                            // *** VERIFICAR MÚLTIPLES CAMPOS DE PROBABILIDAD ***
                                            let prob = 0;
                                            if (notification.data.probabilidad !== undefined && notification.data.probabilidad !== null) {
                                                prob = notification.data.probabilidad;
                                            } else if (notification.data.probability !== undefined && notification.data.probability !== null) {
                                                prob = notification.data.probability;
                                            } else if (notification.data.probabilidad_violencia !== undefined && notification.data.probabilidad_violencia !== null) {
                                                prob = notification.data.probabilidad_violencia;
                                            }

                                            return `${(prob * 100).toFixed(1)}%`;
                                        })()}
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium">Personas:</span>
                                    <span className="ml-1 font-bold">
                                        {notification.data.personas_detectadas ||
                                            notification.data.peopleCount ||
                                            0}
                                    </span>
                                </div>
                                {(notification.data.ubicacion || notification.data.location) && (
                                    <div className="col-span-2">
                                        <span className="font-medium">Ubicación:</span>
                                        <span className="ml-1 font-semibold text-red-700">
                                            {notification.data.ubicacion || notification.data.location}
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {/* *** MODIFICAR: Barra de progreso con tiempo específico *** */}
            <div className="mt-3 h-1 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-300 ease-linear ${
                        notification.type === 'violence' ? 'bg-red-500' :
                        notification.type === 'error' ? 'bg-red-400' :
                        notification.type === 'warning' ? 'bg-yellow-400' :
                        'bg-blue-400'
                    }`}
                    style={{
                        width: '100%',
                        animation: `shrink ${
                            notification.type === 'violence' ? '8s' :
                            notification.type === 'error' ? '10s' : '6s'
                        } linear forwards`
                    }}
                />
            </div>
        </div>
    );
};

// Hook para sonidos de notificación
const useNotificationSound = () => {
    const audioRef = useRef(null);

    const playSound = (type) => {
        if (!audioRef.current) {
            audioRef.current = new Audio();
        }

        const soundUrls = {
            violence: '/sounds/alert-critical.mp3',
            error: '/sounds/alert-error.mp3',
            warning: '/sounds/alert-warning.mp3',
            info: '/sounds/notification.mp3',
            success: '/sounds/success.mp3'
        };

        audioRef.current.src = soundUrls[type] || soundUrls.info;
        audioRef.current.play().catch(e => {
            console.log('No se pudo reproducir sonido:', e);
        });
    };

    return { playSound };
};

// Componente principal del sistema de notificaciones
const NotificationSystem = ({
    notifications = [],
    onClose,
    onAction,
    maxVisible = 5,
    position = 'top-right',
    soundEnabled = true
}) => {
    const [visibleNotifications, setVisibleNotifications] = useState([]);
    const { playSound } = useNotificationSound();

    useEffect(() => {
        // Mostrar solo las notificaciones más recientes
        const recent = notifications.slice(0, maxVisible);
        setVisibleNotifications(recent);

        // Reproducir sonido para notificaciones nuevas
        if (soundEnabled && notifications.length > 0) {
            const latestNotification = notifications[0];
            if (latestNotification.type === 'violence' || latestNotification.type === 'error') {
                playSound(latestNotification.type);
            }
        }
    }, [notifications, maxVisible, soundEnabled]);

    const getPositionClasses = () => {
        const positions = {
            'top-right': 'top-4 right-4',
            'top-left': 'top-4 left-4',
            'bottom-right': 'bottom-4 right-4',
            'bottom-left': 'bottom-4 left-4',
            'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
            'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
        };
        return positions[position] || positions['top-right'];
    };

    if (visibleNotifications.length === 0) { return null; }

    return (
        <>
            {/* Estilos CSS para la animación */}
            <style jsx>{`
                @keyframes shrink {
                    from { width: 100%; }
                    to { width: 0%; }
                }
            `}</style>

            <div className={`fixed ${getPositionClasses()} z-50 w-96 max-w-sm space-y-2`}>
                {visibleNotifications.map((notification) => (
                    <NotificationItem
                        key={notification.id}
                        notification={notification}
                        onClose={onClose}
                        onAction={onAction}
                    />
                ))}

                {/* Contador de notificaciones adicionales */}
                {notifications.length > maxVisible && (
                    <div className="text-center">
                        <button
                            className="text-sm text-gray-600 hover:text-gray-800 bg-white px-3 py-1 rounded-full shadow-md border"
                            onClick={() => onAction('show_all')}
                        >
                            +{notifications.length - maxVisible} más notificaciones
                        </button>
                    </div>
                )}
            </div>
        </>
    );
};

// Hook personalizado para manejar notificaciones
export const useNotifications = () => {
    const [notifications, setNotifications] = useState([]);

    const addNotification = (type, message, data = {}, options = {}) => {
        const notification = {
            id: Date.now() + Math.random(),
            type, // 'violence', 'error', 'warning', 'info', 'success'
            message,
            title: options.title,
            details: options.details,
            data, // *** DATOS COMPLETOS INCLUYENDO PROBABILIDAD REAL, PERSONAS Y UBICACIÓN ***
            timestamp: new Date(),
            read: false,
            persistent: options.persistent || false
        };

        console.log("🔔 Agregando notificación con datos:", {
            type,
            message,
            probabilidad: data.probabilidad || data.probability,
            personas: data.personas_detectadas || data.peopleCount,
            ubicacion: data.ubicacion || data.location
        });

        setNotifications(prev => [notification, ...prev]);

        // *** NUEVA LÓGICA: Auto-remove con tiempos específicos para violencia ***
        if (!notification.persistent) {
            let autoRemoveTime;
            
            if (type === 'violence') {
                autoRemoveTime = 8000; // 8 segundos para violencia (más tiempo para que se note)
            } else if (type === 'error') {
                autoRemoveTime = 10000; // 10 segundos para errores
            } else {
                autoRemoveTime = 6000; // 6 segundos para otras notificaciones
            }

            setTimeout(() => {
                removeNotification(notification.id);
            }, autoRemoveTime);
        }

        return notification.id;
    };

    // *** NUEVA FUNCIÓN: Limpiar notificaciones de violencia específicamente ***
    const clearViolenceNotifications = () => {
        setNotifications(prev => prev.filter(n => n.type !== 'violence'));
        console.log('🧹 Notificaciones de violencia limpiadas');
    };

    const removeNotification = (id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const clearAllNotifications = () => {
        setNotifications([]);
    };

    const markAsRead = (id) => {
        setNotifications(prev =>
            prev.map(n => n.id === id ? { ...n, read: true } : n)
        );
    };

    const getUnreadCount = () => {
        return notifications.filter(n => !n.read).length;
    };

    const getNotificationsByType = (type) => {
        return notifications.filter(n => n.type === type);
    };

    return {
        notifications,
        addNotification,
        removeNotification,
        clearAllNotifications,
        clearViolenceNotifications, // *** NUEVA FUNCIÓN ***
        markAsRead,
        getUnreadCount,
        getNotificationsByType
    };
};

// Componente de resumen de notificaciones para la barra superior
export const NotificationSummary = ({ notifications, onClick }) => {
    const unreadCount = notifications.filter(n => !n.read).length;
    const hasViolence = notifications.some(n => n.type === 'violence' && !n.read);
    const hasErrors = notifications.some(n => n.type === 'error' && !n.read);

    return (
        <button
            onClick={onClick}
            className={`relative p-2 rounded-lg transition-colors ${hasViolence ? 'bg-red-100 hover:bg-red-200 text-red-800' :
                hasErrors ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-800' :
                    unreadCount > 0 ? 'bg-blue-100 hover:bg-blue-200 text-blue-800' :
                        'bg-gray-100 hover:bg-gray-200 text-gray-600'
                }`}
        >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M15 17h5l-5 5v-5zM19 12H5l7-7 7 7z" />
            </svg>

            {unreadCount > 0 && (
                <span className={`absolute -top-1 -right-1 h-5 w-5 rounded-full text-xs font-bold text-white flex items-center justify-center ${hasViolence ? 'bg-red-600' :
                    hasErrors ? 'bg-yellow-600' :
                        'bg-blue-600'
                    }`}>
                    {unreadCount > 9 ? '9+' : unreadCount}
                </span>
            )}

            {hasViolence && (
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-600 rounded-full animate-pulse" />
            )}
        </button>
    );
};

// Contexto de notificaciones para uso global
import { createContext, useContext } from 'react';

const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
    const notificationSystem = useNotifications();

    return (
        <NotificationContext.Provider value={notificationSystem}>
            {children}
        </NotificationContext.Provider>
    );
};

export const useNotificationContext = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotificationContext must be used within a NotificationProvider');
    }
    return context;
};

export default NotificationSystem;