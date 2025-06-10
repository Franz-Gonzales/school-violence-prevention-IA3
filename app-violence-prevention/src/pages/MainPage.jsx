import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import Layout from '../components/Layout';
import DashboardContent from './DashboardContent';
import Cameras from './Cameras';
import CameraDetail from './CameraDetail';
import Incidents from './Incidents';
import IncidentDetail from './IncidentDetail';
import NotFound from './NotFound';

const MainPage = () => {
    return (
        <ProtectedRoute>
            <Layout>
                <Routes>
                    <Route path="/dashboard" element={<DashboardContent />} />
                    <Route path="/cameras" element={<Cameras />} />
                    <Route path="/cameras/:cameraId" element={<CameraDetail />} />
                    <Route path="/incidents" element={<Incidents />} />
                    <Route path="/incidents/:incidentId" element={<IncidentDetail />} />
                    <Route path="/reports" element={<div className="p-6"><h1 className="text-2xl font-bold">Informes - En desarrollo</h1></div>} />
                    <Route path="/documents" element={<div className="p-6"><h1 className="text-2xl font-bold">Documentación - En desarrollo</h1></div>} />
                    <Route path="/settings" element={<div className="p-6"><h1 className="text-2xl font-bold">Configuración - En desarrollo</h1></div>} />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </Layout>
        </ProtectedRoute>
    );
};

export default MainPage;