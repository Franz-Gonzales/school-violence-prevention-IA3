import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Auth from '../components/Auth';

const Login = () => {
    const navigate = useNavigate();
    const { login, isAuthenticated } = useAuth();

    React.useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    const handleLoginSuccess = (data) => {
        login(data);
        navigate('/dashboard', { replace: true });
    };

    return <Auth onLogin={handleLoginSuccess} />;
};

export default Login;