import React from 'react';
import '../css/home.css';

export default function Home() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const credits = currentUser?.credits ?? 0; // Use nullish coalescing for default value

    return (
        <div className="home-container">
            <h1>Welcome, {currentUser?.username}!</h1>
            <div className="dashboard">
                <div className="stats-card">
                    <h3>Your Credits</h3>
                    <p>{credits}</p>
                </div>
                <div className="stats-card">
                    <h3>Generated Images</h3>
                    <p>0</p>
                </div>
                <div className="stats-card">
                    <h3>Gallery Items</h3>
                    <p>0</p>
                </div>
            </div>
        </div>
    );
} 