import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../css/login.css';

export default function Login() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/v1/login', formData, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = response.data;
            const userInfo = {
                username: data.username,
                isAdmin: data.is_admin,
                credits: data.credits,
                token: data.access_token
            };
            localStorage.setItem('currentUser', JSON.stringify(userInfo));
            localStorage.setItem('jwtToken', data.access_token); // 必须要有这行
            navigate('/');
        } catch (err) {
            console.error('Login error:', err);
            setError(err.response?.data?.error || 'An error occurred during login');
        }
    };

    return (
        <div className="login-container">
            <h1>Login</h1>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">Username:</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password:</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                    />
                </div>
                <button type="submit">Login</button>
            </form>
            <p className="register-link">
                Not a user? <a href="/register">Register</a>
            </p>
        </div>
    );
}