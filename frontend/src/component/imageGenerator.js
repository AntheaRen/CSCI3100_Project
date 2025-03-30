import React, { useState } from 'react';
import '../css/imageGenerator.css';
import axios from 'axios';

export default function ImageGenerator() {
    const [prompt, setPrompt] = useState('');
    const [negativePrompt, setNegativePrompt] = useState('');
    const [settings, setSettings] = useState({
        samplingSteps: 32,
        width: 832,
        height: 1216,
        batchCount: 1,  // 初始值更改为 1 保证安全
        batchSize: 1,
        cfgScale: 1.2,
        seed: ''
    });
    const [generatedImages, setGeneratedImages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const getAuthHeader = () => {
        const token = localStorage.getItem('jwtToken');
        console.log('token:', token);
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const requestData = {
                prompt,
                negativePrompt,
                settings: {
                    ...settings,
                    samplingSteps: Number(settings.samplingSteps),
                    width: Number(settings.width),
                    height: Number(settings.height),
                    batchCount: Number(settings.batchCount),
                    batchSize: Number(settings.batchSize),
                    cfgScale: Number(settings.cfgScale),
                    seed: settings.seed || undefined
                }
            };

            const response = await axios.post(
                'http://127.0.0.1:5000/api/v1/t2i',
                requestData,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    }
                }
            );

            setGeneratedImages(response.data.images || []);

        } catch (err) {
            setError(err.response?.data?.error || 'Generation failed');
            console.error('Generation error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = (name, value) => {
        setSettings(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSave = () => {
        generatedImages.forEach((base64Data, index) => {
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${base64Data}`;
            link.download = `generated_image_${index + 1}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            handleGenerate(e);
        }
    };

    return (
        <div className="image-generator-container">
            <div className="left-panel">
                <div className="prompt-section">
                    <textarea
                        placeholder="Enter your prompt here..."
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        className="prompt-input"
                        onKeyDown={handleKeyDown}
                    />
                    <textarea
                        placeholder="Negative prompt (press Ctrl+Enter or Alt+Enter to generate)"
                        value={negativePrompt}
                        onChange={(e) => setNegativePrompt(e.target.value)}
                        className="prompt-input"
                        onKeyDown={handleKeyDown}
                    />
                </div>

                <div className="settings-section">
                    <div className="setting-group">
                        <label>Sampling Steps</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="1"
                                max="50"
                                value={settings.samplingSteps}
                                onChange={(e) => handleSettingChange('samplingSteps', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.samplingSteps}
                                onChange={(e) => handleSettingChange('samplingSteps', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Width</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="64"
                                max="2048"
                                value={settings.width}
                                onChange={(e) => handleSettingChange('width', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.width}
                                onChange={(e) => handleSettingChange('width', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Height</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="64"
                                max="2048"
                                value={settings.height}
                                onChange={(e) => handleSettingChange('height', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.height}
                                onChange={(e) => handleSettingChange('height', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>CFG Scale</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="1"
                                max="20"
                                value={settings.cfgScale}
                                onChange={(e) => handleSettingChange('cfgScale', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.cfgScale}
                                onChange={(e) => handleSettingChange('cfgScale', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>BatchSize</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="1"
                                max="4"
                                value={settings.batchSize}
                                onChange={(e) => handleSettingChange('batchSize', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.batchSize}
                                onChange={(e) => handleSettingChange('batchSize', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>BatchCount</label>
                        <div className="setting-control">
                            <input
                                type="range"
                                min="1"
                                max="9"
                                value={settings.batchCount}
                                onChange={(e) => handleSettingChange('batchCount', e.target.value)}
                            />
                            <input
                                type="number"
                                value={settings.batchCount}
                                onChange={(e) => handleSettingChange('batchCount', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Seed</label>
                        <input
                            type="text"
                            value={settings.seed}
                            onChange={(e) => handleSettingChange('seed', e.target.value)}
                            placeholder="Enter seed (optional)"
                        />
                    </div>
                </div>
            </div>

            <div className="right-panel">
                <div className="generate-section">
                    <button onClick={handleGenerate} className="generate-button">
                        Generate
                    </button>
                    <div className="style-selectors">
                        <select className="style-select">
                            <option value="none">None</option>
                            {/* Add more style options here */}
                        </select>
                        <select className="style-select">
                            <option value="none">None</option>
                            {/* Add more style options here */}
                        </select>
                    </div>
                </div>

                <div className="image-preview">
                    {loading ? (
                        <div className="loading-indicator">
                            <div className="spinner"></div>
                            <p>Generating...</p>
                        </div>
                    ) : generatedImages.length > 0 ? (
                        generatedImages.map((base64Data, index) => (
                            <img
                                key={index}
                                src={`data:image/png;base64,${base64Data}`}
                                alt={`Generated ${index + 1}`}
                                className="generated-image"
                            />
                        ))
                    ) : (
                        <div className="placeholder">No images generated yet</div>
                    )}
                </div>

                <div className="action-buttons">
                    <button
                        onClick={handleSave}
                        disabled={generatedImages.length === 0}
                        className="download-button"
                    >
                        📥
                    </button>
                    {/* <button>Zip</button>
                    <button>Send to img2img</button>
                    <button>Send to inpaint</button>
                    <button>Send to extras</button> */}
                </div>
            </div>
        </div>
    );
}