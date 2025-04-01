import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/gallery.css';

export default function Gallery() {
    const [images, setImages] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchImages = async () => {
            try {
                const currentUser = JSON.parse(localStorage.getItem('currentUser'));
                if (!currentUser || !currentUser.token) {
                    throw new Error('No authentication token found');
                }

                const response = await axios.get(
                    `http://127.0.0.1:5000/api/v1/images/user/${currentUser.id}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${currentUser.token}`,
                            'Content-Type': 'application/json'
                        }
                    }
                );

                console.log(response.data.images);

                setImages(response.data.images || []);
                for (const image of response.data.images) {
                    console.log(`Image path: /outputs/t2i/user_${image.user_id}/image_${image.id}.png`);
                }
            } catch (err) {
                console.error('Error fetching images:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchImages();
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (images.length === 0) return <div>No images found</div>;

    return (
        <div className="gallery-container">
            <h1>Your Generated Images</h1>
            <div className="gallery-grid">
                {images.map((image) => (
                    <div key={image.id} className="gallery-item">
                        <div className="image-container">
                            <img 
                                //src={`http://localhost:3000/outputs/t2i/user_${image.user_id}/image_${image.id}.png`}
                                src={`http://127.0.0.1:5000/static/user_${image.user_id}/image_${image.id}.png`} 
                                alt={image.prompt} 
                            />
                            <div className="image-overlay">
                                <div className="image-actions">
                                    <button 
                                        className="action-button download"
                                        onClick={() => {
                                            console.log('Download button clicked');
                                            const link = document.createElement('a');
                                            link.href = `http://127.0.0.1:5000/static/user_${image.user_id}/image_${image.id}.png`;
                                            link.setAttribute('download', `image_${image.id}.png`);
                                            document.body.appendChild(link);
                                            console.log('Link created:', link);
                                            link.click();
                                            console.log('Link clicked');
                                            document.body.removeChild(link);
                                            console.log('Link removed');
                                        }}
                                    >
                                        Download
                                    </button>
                                    <button className="action-button delete">
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="image-info">
                            <p className="prompt">{image.prompt}</p>
                            <p className="date">
                                {new Date(image.created_at).toLocaleString()}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
