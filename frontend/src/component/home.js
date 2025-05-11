import React, { useEffect, useState } from 'react';
import '../css/home.css';

export default function Home() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // Add state for user data including credits
    const [userData, setUserData] = useState({
        username: currentUser?.username || '',
        credits: currentUser?.credits || 0
    });
    
    // Add state for gallery count
    const [galleryCount, setGalleryCount] = useState(0);
    // Add state for generated images count (for future implementation)
    const [generatedCount, setGeneratedCount] = useState(0);

    useEffect(() => {
        async function fetchUserData() {
            if (!currentUser) return;
            
            try {
                // Fetch the latest user data including credits
                const response = await fetch(`http://localhost:5000/api/v1/users/${currentUser.username}`, {
                    headers: {
                        'Authorization': `Bearer ${currentUser?.token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch user data');
                }

                const data = await response.json();
                setUserData({
                    username: data.username,
                    credits: data.credits
                });
            } catch (error) {
                console.error('Error fetching user data:', error);
            }
        }
        
        async function fetchGalleryCount() {
            if (!currentUser) return;
            
            try {
                const response = await fetch('http://localhost:5000/api/v1/gallery/count', {
                    headers: {
                        'Authorization': `Bearer ${currentUser?.token}`
                    }
                });

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    console.error('Non-JSON response body:', text);
                    throw new Error('Response is not JSON');
                }

                const data = await response.json();
                setGalleryCount(data.count);
            } catch (error) {
                console.error('Error fetching gallery count:', error);
                setGalleryCount(0);
            }
        }
    
        if (currentUser) {
            fetchUserData();
            fetchGalleryCount();
        }
    }, [currentUser]);

    return (
        <div className="home-container">
            <h1>Welcome, {userData.username}!</h1>
            <div className="dashboard">
                <div className="stats-card">
                    <h3>Your Credits</h3>
                    <p>{userData.credits}</p>
                </div>
                <div className="stats-card">
                    <h3>Generated Images</h3>
                    <p>{generatedCount}</p>
                </div>
                <div className="stats-card">
                    <h3>Gallery Items</h3>
                    <p>{galleryCount}</p>
                </div>
            </div>
        </div>
    );
} 