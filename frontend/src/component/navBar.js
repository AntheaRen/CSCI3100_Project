import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/navBar.css';

export default function NavBar() {
    const navigate = useNavigate();
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));

    const handleLogout = async () => {
        try {
            // Call the logout endpoint with JWT token
            await axios.post('http://127.0.0.1:5000/api/v1/logout', {}, {
                headers: {
                    'Authorization': `Bearer ${currentUser?.token}`,
                    'Content-Type': 'application/json'
                }
            });

            // Clear user data from localStorage
            localStorage.removeItem('currentUser');
            navigate('/login');
        } catch (err) {
            console.error('Logout error:', err);
            // Even if the server request fails, we should still clear local data
            localStorage.removeItem('currentUser');
            navigate('/login');
        }
    };

    return (
        <nav className="navbar">
            <div className="nav-left">
                <Link to="/" className="nav-logo">
                    AI Image Generator
                </Link>
                <div className="nav-links">
                    <Link to="/" className="nav-link">Home</Link>
                    <Link to="/generator" className="nav-link">Generate</Link>
                    <Link to="/gallery" className="nav-link">Gallery</Link>
                    {currentUser?.isAdmin && (
                        <Link to="/admin" className="nav-link admin-link">Admin Panel</Link>
                    )}
                </div>
            </div>
            <div className="nav-right">
                <span className="username">
                    {currentUser?.username}
                    {currentUser?.isAdmin && <span className="admin-badge">Admin</span>}
                </span>
                <button onClick={handleLogout} className="logout-button">
                    Logout
                </button>
            </div>
        </nav>
    );
}
