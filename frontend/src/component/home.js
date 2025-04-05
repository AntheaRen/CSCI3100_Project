import React, { useState, useEffect } from 'react';
import '../css/home.css';

export default function Home() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const credits = currentUser?.credits ?? 0; // Use nullish coalescing for default value
    const [galleryCount, setGalleryCount] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchGalleryCount();
    }, []);

    const fetchGalleryCount = async () => {
        try {
            const token = localStorage.getItem('jwtToken');
            if (token) {
                const response = await fetch('http://127.0.0.1:5000/api/v1/images', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                const data = await response.json();
                if (data.images) {
                    setGalleryCount(data.images.length);
                }
            }
        } catch (error) {
            console.error('Error fetching gallery count:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="home-container">
            <h1>Welcome, {currentUser?.username}!</h1>
            <div className="dashboard">
                <div className="stats-card">
                    <h3>Your Credits</h3>
                    <p>{credits}</p>
                </div>
                <div className="stats-card">
                    <h3>Gallery Items</h3>
                    <p>{loading ? '...' : galleryCount}</p>
                </div>
            </div>
        </div>
    );
}