import ReactDOM from 'react-dom/client';
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Register from './component/register';
import Login from './component/login';
import NavBar from './component/navBar';
import ImageGenerator from './component/imageGenerator';
import Home from './component/home';
import AdminPanel from './component/adminPanel';
import Gallery from './component/gallery';
import './css/protectedLayout.css';

// Default users with proper credits initialization
const defaultUsers = [
    {
        username: 'admin',
        password: 'admin123',
        isAdmin: true,
        credits: 100  // Set initial credits for admin
    },
    {
        username: 'user',
        password: 'user123',
        isAdmin: false,
        credits: 10   // Set initial credits for regular user
    }
];

// Clear existing users and reinitialize
localStorage.removeItem('users');
localStorage.setItem('users', JSON.stringify(defaultUsers));
console.log('Initialized users:', JSON.parse(localStorage.getItem('users')));

// Helper component for protected routes
const ProtectedRoute = ({ children }) => {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const isAuthenticated = !!currentUser;
    
    if (!isAuthenticated) {
        // Redirect to login with the return url
        return <Navigate to="/login" replace state={{ from: window.location.pathname }} />;
    }
    
    // Check if user still exists in the users list
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const userStillExists = users.some(u => u.username === currentUser.username);
    
    if (!userStillExists) {
        // If user was deleted, clear currentUser and redirect to login
        localStorage.removeItem('currentUser');
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