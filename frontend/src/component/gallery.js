import React, { useState } from 'react';
import '../css/gallery.css';

//os.path.join("database", "images", str(self.user_id), f"{self.id}.png")

export default function Gallery() {
    // Example images array - replace with your actual images data
    const [images] = useState([
        {
            id: 1,
            url: 'https://picsum.photos/400/400?random=1',
            prompt: 'A beautiful sunset over mountains',
            date: '2024-01-20'
        },
        {
            id: 2,
            url: 'https://picsum.photos/400/400?random=2',
            prompt: 'A futuristic city skyline',
            date: '2024-01-21'
        },
        {
            id: 3,
            url: 'https://picsum.photos/400/400?random=3',
            prompt: 'An enchanted forest with magical creatures',
            date: '2024-01-22'
        }
    ]);

    return (
        <div className="gallery-container">
            <h1>Your Generated Images</h1>
            <div className="gallery-grid">
                {images.map((image) => (
                    <div key={image.id} className="gallery-item">
                        <div className="image-container">
                            <img src={image.url} alt={image.prompt} />
                            <div className="image-overlay">
                                <div className="image-actions">
                                    <button className="action-button download">
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
                            <p className="date">{image.date}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
