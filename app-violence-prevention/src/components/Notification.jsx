import React from 'react';

const Notification = ({ message, onClose }) => {
    return (
        <div className="fixed top-4 right-4 z-50 max-w-sm">
            <div className="bg-red-500 text-white p-4 rounded-lg shadow-lg flex justify-between items-center">
                <p>{message}</p>
                <button onClick={onClose} className="text-white hover:text-gray-200">
                    ✕
                </button>
            </div>
        </div>
    );
};

export default Notification;