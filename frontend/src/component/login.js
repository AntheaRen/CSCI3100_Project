import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/login.css';

export default function Login() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        isAdmin: null,
        credits: 0
    });
    const [error, setError] = useState('');

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');

        try {
            // Get users from localStorage
            const users = JSON.parse(localStorage.getItem('users') || '[]');
            console.log('Available users:', users);
            console.log('Attempting login with:', formData);
            
            // Find user
            const user = users.find(u => 
                u.username === formData.username && 
                u.password === formData.password
            );
            
            console.log('Found user:', user);

            if (user) {
                // Store all user data except password
                const userInfo = {
                    username: user.username,
                    isAdmin: user.isAdmin,
                    credits: user.credits
                };
                localStorage.setItem('currentUser', JSON.stringify(userInfo));
                navigate('/');
            } else {
                setError('Invalid username or password');
            }
        } catch (err) {
            console.error('Login error:', err);
            setError('An error occurred during login');
        }
    };

    // Log the current users in localStorage when component mounts
    React.useEffect(() => {
        const users = JSON.parse(localStorage.getItem('users') || '[]');
        console.log('Users in localStorage:', users);
    }, []);

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