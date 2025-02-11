import React, { useState } from 'react';
import '../css/imageGenerator.css';

export default function ImageGenerator() {
    const [prompt, setPrompt] = useState('');
    const [negativePrompt, setNegativePrompt] = useState('');
    const [settings, setSettings] = useState({
        samplingSteps: 20,
        width: 512,
        height: 512,
        batchCount: 4,
        batchSize: 1,
        cfgScale: 12,
        seed: ''
    });
    const [generatedImages, setGeneratedImages] = useState([]);

    const handleGenerate = (e) => {
        e.preventDefault();
        // TODO: Add your image generation logic here
        console.log('Generating with settings:', { prompt, negativePrompt, settings });
    };

    const handleSettingChange = (name, value) => {
        setSettings(prev => ({
            ...prev,
            [name]: value
        }));
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
                    />
                    <textarea
                        placeholder="Negative prompt (press Ctrl+Enter or Alt+Enter to generate)"
                        value={negativePrompt}
                        onChange={(e) => setNegativePrompt(e.target.value)}
                        className="prompt-input"
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
                    {/* Preview image will go here */}
                </div>

                <div className="action-buttons">
                    <button>Save</button>
                    <button>Zip</button>
                    <button>Send to img2img</button>
                    <button>Send to inpaint</button>
                    <button>Send to extras</button>
                </div>
            </div>
        </div>
    );
}