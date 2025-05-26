import React from 'react';

const StatCard = ({ title, value, icon, color = 'text-primary' }) => {
    return (
        <div className="stat-card">
            <div>
                <h3 className="text-sm font-medium text-gray-600">{title}</h3>
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
            </div>
            {icon && <div className={`text-3xl ${color}`}>{icon}</div>}
        </div>
    );
};

export default StatCard;