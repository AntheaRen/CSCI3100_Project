import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../css/navBar.css';

export default function NavBar() {
    const navigate = useNavigate();
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));

    const handleLogout = () => {
        localStorage.removeItem('currentUser');
        navigate('/login');
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
