import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/gallery.css';

export default function Gallery() {
    const [images, setImages] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    const handleDelete = async (imageId) => {
        try {
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (!currentUser || !currentUser.token) {
                throw new Error('No authentication token found');
            }

            await axios.delete(
                `http://127.0.0.1:5000/api/v1/images/${imageId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${currentUser.token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Remove the deleted image from state
            setImages(prevImages => prevImages.filter(img => img.id !== imageId));
            setDeleteConfirm(null); // Close confirmation dialog
        } catch (err) {
            console.error('Error deleting image:', err);
            setError(err.response?.data?.error || 'Failed to delete image');
        }
    };

    const handleDownload = (imageId, imageUrl) => {
        try {
            // Force download by fetching the image first
            fetch(imageUrl)
                .then(response => response.blob())
                .then(blob => {
                    // Create a blob URL
                    const blobUrl = window.URL.createObjectURL(blob);
                    
                    // Create a link element
                    const link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = `image_${imageId}.png`;
                    
                    // Append to body, click and clean up
                    document.body.appendChild(link);
                    link.click();
                    
                    // Clean up
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(blobUrl);
                })
                .catch(error => {
                    console.error('Error downloading image:', error);
                });
        } catch (error) {
            console.error('Error downloading image:', error);
        }
    };

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
            {deleteConfirm && (
                <div className="delete-confirmation">
                    <div className="delete-confirmation-content">
                        <p>Are you sure you want to delete this image?</p >
                        <div className="delete-confirmation-buttons">
                            <button 
                                className="confirm-button"
                                onClick={() => handleDelete(deleteConfirm)}
                            >
                                Yes, Delete
                            </button>
                            <button 
                                className="cancel-button"
                                onClick={() => setDeleteConfirm(null)}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
            <div className="gallery-grid">
                {images.map((image) => (
                    <div key={image.id} className="gallery-item">
                        <div className="image-container">
                            < img 
                                //src={`http://localhost:3000/outputs/t2i/user_${image.user_id}/image_${image.id}.png`}
                                src={`http://127.0.0.1:5000/static/user_${image.user_id}/image_${image.id}.png`} 
                                alt={image.prompt} 
                            />
                            <div className="image-overlay">
                                <div className="image-actions">
                                    <button 
                                        className="action-button download"
                                        onClick={() => handleDownload(image.id, `http://127.0.0.1:5000/static/user_${image.user_id}/image_${image.id}.png`)}
                                    >
                                        Download
                                    </button>
                                    <button 
                                        className="action-button delete"
                                        onClick={() => setDeleteConfirm(image.id)}
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="image-info">
                            <p className="prompt">{image.prompt}</p >
                            <p className="date">
                                {new Date(image.created_at).toLocaleString()}
                            </p >
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}