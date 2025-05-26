import React from 'react';

const NotFound = () => {
    return (
        <div className="flex items-center justify-center min-h-screen bg-background">
            <div className="text-center">
                <h1 className="text-4xl font-bold text-primary">404 - Página no encontrada</h1>
                <p className="text-textPrimary mt-4">Lo sentimos, la página que buscas no existe.</p>
            </div>
        </div>
    );
};

export default NotFound;