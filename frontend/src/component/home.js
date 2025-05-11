import React, { useEffect, useState } from 'react';
import '../css/home.css';

export default function Home() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const credits = currentUser?.credits ?? 0; // Use nullish coalescing for default value

    // Add state for gallery count
    const [galleryCount, setGalleryCount] = useState(0);

    useEffect(() => {
        async function fetchGalleryCount() {
            try {
                // Log the currentUser object
                //console.log('currentUser:', currentUser);
    
                // Log the token being used
                //console.log('Token used:', currentUser?.token);
    
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
            fetchGalleryCount();
        }
    }, [currentUser]);

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
                    <p>{galleryCount}</p>
                </div>
            </div>
        </div>
    );
} 