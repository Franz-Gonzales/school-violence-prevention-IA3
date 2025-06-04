import React, { useState, useEffect, useRef } from 'react';

// Componente de notificación individual
const NotificationItem = ({ notification, onClose, onAction }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [isClosing, setIsClosing] = useState(false);

    useEffect(() => {
        setIsVisible(true);

        // Auto-close después del tiempo especificado
        const autoCloseTime = notification.type === 'violence' ? 15000 :
            notification.type === 'error' ? 8000 : 5000;

        const timer = setTimeout(() => {
            handleClose();
        }, autoCloseTime);

        return () => clearTimeout(timer);
    }, []);

    const handleClose = () => {
        setIsClosing(true);
        setTimeout(() => {
            onClose(notification.id);
        }, 300);
    };

    const getNotificationStyles = () => {
        const baseStyles = "transform transition-all duration-300 ease-in-out";
        const typeStyles = {
            violence: "bg-red-50 border-l-4 border-red-500 shadow-lg",
            error: "bg-red-50 border-l-4 border-red-400 shadow-md",
            warning: "bg-yellow-50 border-l-4 border-yellow-400 shadow-md",
            info: "bg-blue-50 border-l-4 border-blue-400 shadow-md",
            success: "bg-green-50 border-l-4 border-green-400 shadow-md"
        };

        const visibilityStyles = isVisible && !isClosing
            ? "translate-x-0 opacity-100"
            : "translate-x-full opacity-0";

        return `${baseStyles} ${typeStyles[notification.type] || typeStyles.info} ${visibilityStyles}`;
    };

    const getIcon = () => {
        const icons = {
            violence: "🚨",
            error: "❌",
            warning: "⚠️",
            info: "ℹ️",
            success: "✅"
        };
        return icons[notification.type] || "📢";
    };

    const getTextColor = () => {
        const colors = {
            violence: "text-red-800",
            error: "text-red-700",
            warning: "text-yellow-700",
            info: "text-blue-700",
            success: "text-green-700"
        };
        return colors[notification.type] || "text-gray-700";
    };

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
                        <div className="text-xs text-gray-500 mt-2">
                            {notification.timestamp.toLocaleTimeString()}
                        </div>

                        {/* Datos específicos para alertas de violencia */}
                        {notification.type === 'violence' && notification.data && (
                            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="font-medium">Probabilidad:</span>
                                    <span className="ml-1 font-bold text-red-600">
                                        {(notification.data.probability * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div>
                                    <span className="font-medium">Personas:</span>
                                    <span className="ml-1 font-bold">
                                        {notification.data.peopleCount}
                                    </span>
                                </div>
                                {notification.data.location && (
                                    <div className="col-span-2">
                                        <span className="font-medium">Ubicación:</span>
                                        <span className="ml-1">{notification.data.location}</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Acciones para notificaciones importantes */}
                        {(notification.type === 'violence' || notification.type === 'error') && (
                            <div className="mt-3 flex space-x-2">
                                {notification.type === 'violence' && (
                                    <>
                                        <button
                                            onClick={() => onAction('view_evidence', notification)}
                                            className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                                        >
                                            Ver Evidencia
                                        </button>
                                        <button
                                            onClick={() => onAction('notify_authorities', notification)}
                                            className="px-3 py-1 text-xs bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
                                        >
                                            Notificar Autoridades
                                        </button>
                                    </>
                                )}
                                <button
                                    onClick={() => onAction('acknowledge', notification)}
                                    className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                                >
                                    Reconocer
                                </button>
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

            {/* Barra de progreso para auto-close */}
            <div className="mt-3 h-1 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-300 ease-linear ${notification.type === 'violence' ? 'bg-red-500' :
                            notification.type === 'error' ? 'bg-red-400' :
                                notification.type === 'warning' ? 'bg-yellow-400' :
                                    'bg-blue-400'
                        }`}
                    style={{
                        width: '100%',
                        animation: `shrink ${notification.type === 'violence' ? '15s' :
                            notification.type === 'error' ? '8s' : '5s'} linear forwards`
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

    if (visibleNotifications.length === 0) {return null;}

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
            data,
            timestamp: new Date(),
            read: false,
            persistent: options.persistent || false
        };

        setNotifications(prev => [notification, ...prev]);

        // Auto-remove si no es persistente
        if (!notification.persistent) {
            const autoRemoveTime = type === 'violence' ? 20000 :
                type === 'error' ? 10000 : 6000;

            setTimeout(() => {
                removeNotification(notification.id);
            }, autoRemoveTime);
        }

        return notification.id;
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