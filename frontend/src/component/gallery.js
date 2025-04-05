import React, { useState, useEffect } from 'react';
import '../css/gallery.css';

export default function Gallery() {
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchImages();
    }, []);

    const fetchImages = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('jwtToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (token && currentUser) {
                // First fetch the list of images
                const response = await fetch('http://127.0.0.1:5000/api/v1/images', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                const data = await response.json();
                if (data.images && data.images.length > 0) {
                    // Create initial image objects with loading state
                    const formattedImages = data.images.map(img => ({
                        id: img.id,
                        url: null, // Will be populated with base64 data
                        prompt: img.prompt || 'No prompt available',
                        date: new Date(img.created_at).toLocaleDateString(),
                        loading: true
                    }));
                    setImages(formattedImages);
                    
                    // Fetch each image's data individually
                    const imagePromises = formattedImages.map(async (img) => {
                        try {
                            const imgResponse = await fetch(`http://127.0.0.1:5000/api/v1/images/${img.id}`, {
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                            const imgData = await imgResponse.json();
                            
                            if (imgData.image_data) {
                                return {
                                    ...img,
                                    url: `data:image/png;base64,${imgData.image_data}`,
                                    loading: false
                                };
                            }
                            return { ...img, loading: false, error: true };
                        } catch (error) {
                            console.error(`Error fetching image ${img.id}:`, error);
                            return { ...img, loading: false, error: true };
                        }
                    });
                    
                    // Wait for all image fetches to complete
                    const updatedImages = await Promise.all(imagePromises);
                    setImages(updatedImages);
                    setLoading(false);
                } else {
                    setImages([]);
                    setLoading(false);
                }
            } else {
                setImages([]);
                setLoading(false);
            }
        } catch (error) {
            console.error('Error fetching images:', error);
            setImages([]);
            setLoading(false);
        }
    };

    const handleDownload = (imageId, imageUrl) => {
        try {
            // The imageUrl is already a data URL with base64 data
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `image_${imageId}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading image:', error);
        }
    };

    const handleDelete = async (imageId) => {
        try {
            const token = localStorage.getItem('jwtToken');
            if (!token) {
                console.error('No authentication token found');
                return;
            }
            
            // Call the backend API to delete the image
            const response = await fetch(`http://127.0.0.1:5000/api/v1/images/${imageId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete image: ${response.statusText}`);
            }
            
            // Remove the image from the local state
            setImages(images.filter(img => img.id !== imageId));
        } catch (error) {
            console.error('Error deleting image:', error);
        }
    };

    return (
        <div className="gallery-container">
            <h1>Your Generated Images</h1>
            {loading ? (
                <div className="loading-message">Loading your images...</div>
            ) : images.length > 0 ? (
                <div className="gallery-grid">
                    {images.map((image) => (
                        <div key={image.id} className="gallery-item">
                            <div className="image-container">
                                {image.loading ? (
                                    <div className="loading-image">Loading image...</div>
                                ) : image.error ? (
                                    <div className="error-image">Failed to load image</div>
                                ) : (
                                    <img src={image.url} alt={image.prompt} />
                                )}
                                {!image.loading && !image.error && (
                                    <div className="image-overlay">
                                        <div className="image-actions">
                                            <button 
                                                className="action-button download"
                                                onClick={() => handleDownload(image.id, image.url)}
                                                disabled={!image.url}
                                            >
                                                Download
                                            </button>
                                            <button 
                                                className="action-button delete"
                                                onClick={() => handleDelete(image.id)}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="image-info">
                                <p className="prompt">{image.prompt}</p>
                                <p className="date">{image.date}</p>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="no-images-message">
                    <p>You haven't generated any images yet.</p>
                    <p>Go to the Image Generator to create some!</p>
                </div>
            )}
        </div>
    );
}