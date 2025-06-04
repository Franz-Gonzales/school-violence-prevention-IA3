import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './components/NotificationSystem';
import Login from './pages/Login';
import MainPage from './pages/MainPage';
import NotFound from './pages/NotFound';

function App() {
    return (
        <AuthProvider>
            <NotificationProvider>
                <Router>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/*" element={<MainPage />} />
                        <Route path="/not-found" element={<NotFound />} />
                        <Route path="/" element={<Navigate to="/dashboard" />} />
                    </Routes>
                </Router>
            </NotificationProvider>
        </AuthProvider>
    );
}

export default App;