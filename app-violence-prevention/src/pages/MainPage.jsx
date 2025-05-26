import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from '../components/Layout';
import DashboardContent from './DashboardContent';
import Cameras from './Cameras';
import CameraDetail from './CameraDetail';
import Incidents from './Incidents';
import Reports from './Reports';
import Documents from './Documents';
import Settings from './Settings';

const MainPage = () => {
    return (
        <Layout>
            <Routes>
                <Route path="/dashboard" element={<DashboardContent />} />
                <Route path="/cameras" element={<Cameras />} />
                <Route path="/cameras/:cameraId" element={<CameraDetail />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
        </Layout>
    );
};

export default MainPage;