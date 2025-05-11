import ReactDOM from 'react-dom/client';
import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
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


const ProtectedLayout = () => {
    const location = useLocation();
    const [cache] = useState({
        home: <Home />,
        generator: <ImageGenerator />,
        gallery: <Gallery />,
        upscale: <Upscale />,
        admin: <AdminPanel />
    });

    // 获取基础路径（处理可能的尾部斜杠）
    const basePath = location.pathname.split('/')[1] || 'home';

    return (
        <div className="app-container">
            <NavBar />
            <main className="main-content">
                <div style={{ display: basePath === 'home' ? 'block' : 'none' }}>
                    {cache.home}
                </div>
                <div style={{ display: basePath === 'generator' ? 'block' : 'none' }}>
                    {cache.generator}
                </div>
                <div style={{ display: basePath === 'gallery' ? 'block' : 'none' }}>
                    {cache.gallery}
                </div>
                <div style={{ display: basePath === 'upscale' ? 'block' : 'none' }}>
                    {cache.upscale}
                </div>
                <div style={{ display: basePath === 'admin' ? 'block' : 'none' }}>
                    {cache.admin}
                </div>
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
                    <Route index element={<div />} /> // 空元素
                    <Route path="home" element={<div />} />
                    <Route path="generator" element={<div />} />
                    <Route path="gallery" element={<div />} />
                    <Route path="upscale" element={<div />} />
                    <Route path="admin" element={<div />} />
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