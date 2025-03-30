import ReactDOM from 'react-dom/client';
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Register from './component/register';
import Login from './component/login';
import NavBar from './component/navBar';
import ImageGenerator from './component/imageGenerator';
import Home from './component/home';
import AdminPanel from './component/adminPanel';
import Gallery from './component/gallery';
import Upscale from './component/upscale';
import './css/protectedLayout.css';
import axios from 'axios';

// Helper component for protected routes
const ProtectedRoute = ({ children }) => {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    console.log('Protected Route - Current User:', currentUser);
    
    useEffect(() => {
        const verifyToken = async () => {
            try {
                const response = await axios.get('http://localhost:5000/api/v1/verify-token', {
                    headers: {
                        'Authorization': `Bearer ${currentUser?.token}`
                    }
                });
                if (!response.data.valid) {
                    localStorage.clear();
                    window.location.href = '/login';
                }
            } catch (error) {
                localStorage.clear();
                window.location.href = '/login';
            }
        };

        if (currentUser?.token) {
            verifyToken();
        }
    }, []);

    if (!currentUser) {
        console.log('No user found, redirecting to login');
        return <Navigate to="/login" replace />;
    }
    
    return children;
};

// Protected Layout Component
const ProtectedLayout = () => {
    return (
        <div className="app-container">
            <NavBar />
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
};

const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Routes */}
                <Route path="/" element={
                    <ProtectedRoute>
                        <ProtectedLayout />
                    </ProtectedRoute>
                }>
                    <Route index element={<Home />} />
                    <Route path="home" element={<Home />} />
                    <Route path="generator" element={<ImageGenerator />} />
                    <Route path="gallery" element={<Gallery />} />
                    <Route path="upscale" element={<Upscale />} />
                    
                    {/* Admin only route */}
                    <Route path="admin" element={
                        <AdminRoute>
                            <AdminPanel />
                        </AdminRoute>
                    } />
                </Route>

                {/* Catch all route - redirect to home */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    );
};

// Add AdminRoute component for admin-only pages
const AdminRoute = ({ children }) => {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const isAdmin = currentUser?.isAdmin;

    if (!isAdmin) {
        return <Navigate to="/" replace />;
    }

    return children;
};

const root = ReactDOM.createRoot(document.getElementById('app'));
root.render(<App />);