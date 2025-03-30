import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/adminPanel.css';

export default function AdminPanel() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editingUser, setEditingUser] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const [createForm, setCreateForm] = useState({
        username: '',
        password: '',
        credits: 0
    });
    const [editForm, setEditForm] = useState({
        username: '',
        password: '',
        credits: 0
    });

    // Fetch users on component mount
    useEffect(() => {
        fetchUsers();
    }, []);
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const fetchUsers = async () => {
        try {
            const token = currentUser.token;
            console.log('Token:', token);

            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
            console.log('Headers:', headers);

            const response = await axios.get('http://localhost:5000/api/v1/users', { headers });
            console.log('Response:', response.data);
            
            setUsers(response.data || []);
            setLoading(false);
        } catch (err) {
            console.error('Full error:', err);
            console.error('Error response:', err.response?.data);
            setError(err.response?.data?.error || 'Failed to fetch users');
            setLoading(false);
        }
    };

    const handleEdit = (user) => {
        setEditingUser(user);
        setEditForm({
            username: user.username,
            password: '',
            credits: user.credits
        });
    };

    const handleUpdate = async () => {
        try {
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            const token = currentUser.token;
            
            // Format the data to match backend expectations
            const updateData = {
                username: editForm.username,
                password: editForm.password,
                credits: Number(editForm.credits)
            };

            // Only include password if it was entered
            if (!updateData.password) {
                delete updateData.password;
            }

            await axios.put(`http://localhost:5000/api/v1/users/${editingUser.username}`, updateData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            setEditingUser(null);
            fetchUsers(); // Refresh user list
        } catch (err) {
            console.error('Update error:', err.response?.data);
            setError(err.response?.data?.message || 'Failed to update user');
        }
    };

    const handleDelete = async (username) => {
        if (window.confirm(`Are you sure you want to delete user ${username}?`)) {
            try {
                const currentUser = JSON.parse(localStorage.getItem('currentUser'));
                const token = currentUser.token;
                await axios.delete(`http://localhost:5000/api/v1/users/${username}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                fetchUsers(); // Refresh user list
            } catch (err) {
                setError('Failed to delete user');
            }
        }
    };

    const handleCreate = async () => {
        try {
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            const token = currentUser.token;

            await axios.post('http://localhost:5000/api/v1/users', createForm, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            setIsCreating(false);
            setCreateForm({ username: '', password: '', credits: 0 });
            fetchUsers(); // Refresh user list
        } catch (err) {
            console.error('Create error:', err.response?.data);
            setError(err.response?.data?.message || 'Failed to create user');
        }
    };

    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="admin-panel">
            <h1>Admin Panel</h1>
            
            <div className="panel-header">
                <button 
                    className="create-btn"
                    onClick={() => setIsCreating(true)}
                >
                    Create New User
                </button>
            </div>

            <div className="user-management">
                <h2>User Management</h2>
                <table className="users-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Admin Status</th>
                            <th>Credits</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(user => (
                            <tr key={user.username}>
                                <td>{user.username}</td>
                                <td>{user.is_admin ? 'Admin' : 'User'}</td>
                                <td>{user.credits}</td>
                                <td className="actions">
                                    <button 
                                        className="edit-btn"
                                        onClick={() => handleEdit(user)}
                                    >
                                        Edit
                                    </button>
                                    <button 
                                        className="delete-btn"
                                        onClick={() => handleDelete(user.username)}
                                        disabled={user.is_admin}
                                        style={{ opacity: user.is_admin ? 0.5 : 1 }}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create User Modal */}
            {isCreating && (
                <div className="modal">
                    <div className="modal-content">
                        <h2>Create New User</h2>
                        <div className="form-group">
                            <label>Username:</label>
                            <input
                                type="text"
                                value={createForm.username}
                                onChange={(e) => setCreateForm({
                                    ...createForm,
                                    username: e.target.value
                                })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Password:</label>
                            <input
                                type="password"
                                value={createForm.password}
                                onChange={(e) => setCreateForm({
                                    ...createForm,
                                    password: e.target.value
                                })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Credits:</label>
                            <input
                                type="number"
                                min="0"
                                value={createForm.credits}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    if (value === '') {
                                        setCreateForm({
                                            ...createForm,
                                            credits: ''
                                        });
                                    } else {
                                        setCreateForm({
                                            ...createForm,
                                            credits: Number(value)
                                        });
                                    }
                                }}
                                required
                            />
                        </div>
                        <div className="modal-actions">
                            <button 
                                className="save-btn"
                                onClick={handleCreate}
                            >
                                Create User
                            </button>
                            <button 
                                className="cancel-btn"
                                onClick={() => {
                                    setIsCreating(false);
                                    setCreateForm({ username: '', password: '', credits: 0 });
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit User Modal */}
            {editingUser && (
                <div className="modal">
                    <div className="modal-content">
                        <h2>Edit User: {editingUser.username}</h2>
                        <div className="form-group">
                            <label>Username:</label>
                            <input
                                type="text"
                                value={editForm.username}
                                onChange={(e) => setEditForm({
                                    ...editForm,
                                    username: e.target.value
                                })}
                            />
                        </div>
                        <div className="form-group">
                            <label>New Password (leave blank to keep current):</label>
                            <input
                                type="password"
                                value={editForm.password}
                                onChange={(e) => setEditForm({
                                    ...editForm,
                                    password: e.target.value
                                })}
                                placeholder="Enter new password"
                            />
                        </div>
                        <div className="form-group">
                            <label>Credits:</label>
                            <input
                                type="number"
                                min="0"
                                value={editForm.credits}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    // If empty, set to empty string (not 0)
                                    if (value === '') {
                                        setEditForm({
                                            ...editForm,
                                            credits: ''
                                        });
                                    } else {
                                        // Convert to number and remove leading zeros
                                        setEditForm({
                                            ...editForm,
                                            credits: Number(value)
                                        });
                                    }
                                }}
                            />
                        </div>
                        <div className="modal-actions">
                            <button 
                                className="save-btn"
                                onClick={handleUpdate}
                            >
                                Save Changes
                            </button>
                            <button 
                                className="cancel-btn"
                                onClick={() => setEditingUser(null)}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
} 