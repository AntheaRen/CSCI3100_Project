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
            if (token) {
                const response = await fetch('http://127.0.0.1:5000/api/v1/images', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                const data = await response.json();
                if (data.images && data.images.length > 0) {
                    // Fetch each image's data to get the base64 image content
                    const imagePromises = data.images.map(async (img) => {
                        try {
                            const imgResponse = await fetch(`http://127.0.0.1:5000/api/v1/images/${img.id}`, {
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                            const imgData = await imgResponse.json();
                            return {
                                id: img.id,
                                // Use base64 data for image display
                                url: imgData.image_data ? `data:image/png;base64,${imgData.image_data}` : null,
                                path: img.path,
                                prompt: img.prompt || 'No prompt available',
                                date: new Date(img.created_at).toLocaleDateString()
                            };
                        } catch (err) {
                            console.error(`Error fetching image ${img.id}:`, err);
                            return null;
                        }
                    });
                    
                    const formattedImages = (await Promise.all(imagePromises)).filter(img => img !== null);
                    setImages(formattedImages);
                } else {
                    // No images found, set empty array
                    setImages([]);
                }
            } else {
                setImages([]);
            }
        } catch (error) {
            console.error('Error fetching images:', error);
            setImages([]);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (imageId, imageUrl) => {
        try {
            const token = localStorage.getItem('jwtToken');
            if (!token) {
                console.error('No authentication token found');
                return;
            }
            
            // Fetch the specific image with its data from the backend
            const response = await fetch(`http://127.0.0.1:5000/api/v1/images/${imageId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Convert base64 to blob
            if (data.image_data) {
                const byteCharacters = atob(data.image_data);
                const byteNumbers = new Array(byteCharacters.length);
                
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], {type: 'image/png'});
                
                // Create a temporary link to download the image
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `image_${imageId}.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                // Clean up the URL object
                URL.revokeObjectURL(link.href);
            } else {
                // Fallback to the original method for external URLs
                const response = await fetch(imageUrl);
                const blob = await response.blob();
                
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `image_${imageId}.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(link.href);
            }
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
                                <img src={image.url} alt={image.prompt} />
                                <div className="image-overlay">
                                    <div className="image-actions">
                                        <button 
                                            className="action-button download"
                                            onClick={() => handleDownload(image.id, image.url)}
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
