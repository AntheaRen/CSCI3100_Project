import React, { useState } from 'react';
import axios from 'axios';
import '../css/upscale.css';

export default function Upscale() {
    const [inputImage, setInputImage] = useState(null);
    const [upscaledImage, setUpscaledImage] = useState(null);
    const [upscaleRatio, setUpscaleRatio] = useState(2);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const getAuthHeader = () => {
        const token = localStorage.getItem('jwtToken');
        console.log('token:', token);
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setInputImage(reader.result);
                setUpscaledImage(null); // Reset upscaled image
            };
            reader.readAsDataURL(file);
        }
    };

    const handleUpscale = async () => {
        if (!inputImage) {
            setError('Please select an image first');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const base64Image = inputImage.split(',')[1];
            const response = await axios.post(
                'http://localhost:5000/api/v1/upscale',
                {
                    image: base64Image,
                    ratio: upscaleRatio
                },
                { // 第三个参数是配置对象
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader(),
                    }
                }
            );

            if (response.data.image) {
                setUpscaledImage(`data:image/png;base64,${response.data.image}`);
            } else {
                setError('Failed to upscale image');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Error upscaling image');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="upscale-container">
            <div className="image-section">
                <div className="image-box">
                    <h3>Input Image</h3>
                    {inputImage ? (
                        <img src={inputImage} alt="Input" />
                    ) : (
                        <div className="upload-placeholder">
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleImageUpload}
                                id="image-upload"
                            />
                            <label htmlFor="image-upload">Click to upload image</label>
                        </div>
                    )}
                </div>

                <div className="image-box">
                    <h3>Upscaled Image</h3>
                    {upscaledImage ? (
                        <img src={upscaledImage} alt="Upscaled" />
                    ) : (
                        <div className="placeholder">
                            Upscaled image will appear here
                        </div>
                    )}
                </div>
            </div>

            <div className="controls">
                <div className="ratio-control">
                    <label>Upscale Ratio:</label>
                    <select
                        value={upscaleRatio}
                        onChange={(e) => setUpscaleRatio(Number(e.target.value))}
                    >
                        <option value={2}>2x</option>
                        <option value={4}>4x</option>
                    </select>
                </div>

                <button
                    onClick={handleUpscale}
                    disabled={!inputImage || loading}
                    className="upscale-button"
                >
                    {loading ? 'Processing...' : 'Upscale'}
                </button>
            </div>

            {error && <div className="error-message">{error}</div>}
        </div>
    );
}
