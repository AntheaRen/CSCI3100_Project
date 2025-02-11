import React from 'react';
import '../css/adminPanel.css';

export default function AdminPanel() {
    const [users, setUsers] = React.useState([]);

    React.useEffect(() => {
        // Load users from localStorage
        const allUsers = JSON.parse(localStorage.getItem('users') || '[]');
        setUsers(allUsers);
    }, []);

    return (
        <div className="admin-panel">
            <h1>Admin Panel</h1>
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
                                <td>{user.isAdmin ? 'Admin' : 'User'}</td>
                                <td>{user.credits}</td>
                                <td>
                                    <button className="edit-btn">Edit</button>
                                    <button className="delete-btn">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
} 