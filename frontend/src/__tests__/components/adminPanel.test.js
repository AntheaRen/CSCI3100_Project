import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import AdminPanel from '../../component/adminPanel';

// Mock axios
jest.mock('axios');

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Render with BrowserRouter
const renderWithRouter = (ui) => {
  return render(
    <BrowserRouter>
      {ui}
    </BrowserRouter>
  );
};

describe('AdminPanel Component', () => {
  const mockUsers = [
    {
      username: 'admin',
      is_admin: true,
      credits: 1000
    },
    {
      username: 'user1',
      is_admin: false,
      credits: 100
    },
    {
      username: 'user2',
      is_admin: false,
      credits: 50
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock localStorage to return an admin user
    mockLocalStorage.getItem.mockImplementation(() => JSON.stringify({
      username: 'admin',
      isAdmin: true,
      token: 'fake-admin-token'
    }));
  });

  test('renders loading state initially', () => {
    axios.get.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderWithRouter(<AdminPanel />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders error message when API call fails', async () => {
    // Mock failed API call
    axios.get.mockRejectedValueOnce({
      response: {
        data: {
          error: 'Failed to fetch users'
        }
      }
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch users')).toBeInTheDocument();
    });
  });

  test('renders user table when API call succeeds', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
      expect(screen.getByText('User Management')).toBeInTheDocument();
      
      // Check table headers
      expect(screen.getByText('Username')).toBeInTheDocument();
      expect(screen.getByText('Admin Status')).toBeInTheDocument();
      expect(screen.getByText('Credits')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
      
      // Check if all users are rendered
      expect(screen.getByText('admin')).toBeInTheDocument();
      expect(screen.getByText('user1')).toBeInTheDocument();
      expect(screen.getByText('user2')).toBeInTheDocument();
      
      // Check admin status
      const adminStatuses = screen.getAllByText('Admin');
      const userStatuses = screen.getAllByText('User');
      expect(adminStatuses).toHaveLength(1);
      expect(userStatuses).toHaveLength(2);
      
      // Check credits
      expect(screen.getByText('1000')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      
      // Check action buttons
      const editButtons = screen.getAllByText('Edit');
      const deleteButtons = screen.getAllByText('Delete');
      expect(editButtons).toHaveLength(3);
      expect(deleteButtons).toHaveLength(3);
    });
  });

  test('opens create user modal when Create New User button is clicked', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });
    
    // Click create user button
    fireEvent.click(screen.getByText('Create New User'));
    
    // Check if modal is displayed
    expect(screen.getByText('Create New User', { selector: 'h2' })).toBeInTheDocument();
    expect(screen.getByText('Username:')).toBeInTheDocument();
    expect(screen.getByText('Password:')).toBeInTheDocument();
    expect(screen.getByText('Credits:')).toBeInTheDocument();
    
    // Check if form buttons are displayed
    expect(screen.getByText('Create User')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  test('handles user creation correctly', async () => {
    // Mock successful API calls
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    axios.post.mockResolvedValueOnce({});
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });
    
    // Click create user button
    fireEvent.click(screen.getByText('Create New User'));
    
    // Fill in form
    fireEvent.change(screen.getByLabelText('Username:'), { target: { value: 'newuser' } });
    fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText('Credits:'), { target: { value: '200' } });
    
    // Submit form
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      // Check if API was called with correct parameters
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:5000/api/v1/users',
        {
          username: 'newuser',
          password: 'password123',
          credits: 200
        },
        {
          headers: {
            'Authorization': 'Bearer fake-admin-token',
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Check if users are fetched again
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
  });

  test('handles create user cancellation', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });
    
    // Click create user button
    fireEvent.click(screen.getByText('Create New User'));
    
    // Fill in form
    fireEvent.change(screen.getByLabelText('Username:'), { target: { value: 'newuser' } });
    
    // Click cancel
    fireEvent.click(screen.getByText('Cancel'));
    
    // Check if modal is closed
    expect(screen.queryByText('Create New User', { selector: 'h2' })).not.toBeInTheDocument();
    
    // Check that API was not called
    expect(axios.post).not.toHaveBeenCalled();
  });

  test('opens edit user modal when Edit button is clicked', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Edit')[0]).toBeInTheDocument();
    });
    
    // Click edit button for first user
    fireEvent.click(screen.getAllByText('Edit')[0]);
    
    // Check if modal is displayed
    expect(screen.getByText(`Edit User: ${mockUsers[0].username}`)).toBeInTheDocument();
    expect(screen.getByText('Username:')).toBeInTheDocument();
    expect(screen.getByText('New Password (leave blank to keep current):')).toBeInTheDocument();
    expect(screen.getByText('Credits:')).toBeInTheDocument();
    
    // Check if form buttons are displayed
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    
    // Check if form is pre-filled
    const usernameInput = screen.getByLabelText('Username:');
    const creditsInput = screen.getByLabelText('Credits:');
    expect(usernameInput.value).toBe(mockUsers[0].username);
    expect(creditsInput.value).toBe(mockUsers[0].credits.toString());
  });

  test('handles user update correctly', async () => {
    // Mock successful API calls
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    axios.put.mockResolvedValueOnce({});
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Edit')[1]).toBeInTheDocument();
    });
    
    // Click edit button for second user
    fireEvent.click(screen.getAllByText('Edit')[1]);
    
    // Update form
    fireEvent.change(screen.getByLabelText('Username:'), { target: { value: 'updateduser' } });
    fireEvent.change(screen.getByLabelText('New Password (leave blank to keep current):'), { target: { value: 'newpassword' } });
    fireEvent.change(screen.getByLabelText('Credits:'), { target: { value: '300' } });
    
    // Submit form
    fireEvent.click(screen.getByText('Save Changes'));
    
    await waitFor(() => {
      // Check if API was called with correct parameters
      expect(axios.put).toHaveBeenCalledWith(
        `http://localhost:5000/api/v1/users/${mockUsers[1].username}`,
        {
          username: 'updateduser',
          password: 'newpassword',
          credits: 300
        },
        {
          headers: {
            'Authorization': 'Bearer fake-admin-token',
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Check if users are fetched again
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
  });

  test('handles update with empty password', async () => {
    // Mock successful API calls
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    axios.put.mockResolvedValueOnce({});
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Edit')[1]).toBeInTheDocument();
    });
    
    // Click edit button for second user
    fireEvent.click(screen.getAllByText('Edit')[1]);
    
    // Update form (leave password empty)
    fireEvent.change(screen.getByLabelText('Username:'), { target: { value: 'updateduser' } });
    fireEvent.change(screen.getByLabelText('Credits:'), { target: { value: '300' } });
    
    // Submit form
    fireEvent.click(screen.getByText('Save Changes'));
    
    await waitFor(() => {
      // Check if API was called with correct parameters (no password)
      expect(axios.put).toHaveBeenCalledWith(
        `http://localhost:5000/api/v1/users/${mockUsers[1].username}`,
        {
          username: 'updateduser',
          credits: 300
        },
        {
          headers: {
            'Authorization': 'Bearer fake-admin-token',
            'Content-Type': 'application/json'
          }
        }
      );
    });
  });

  test('handles edit user cancellation', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Edit')[0]).toBeInTheDocument();
    });
    
    // Click edit button for first user
    fireEvent.click(screen.getAllByText('Edit')[0]);
    
    // Click cancel
    fireEvent.click(screen.getByText('Cancel'));
    
    // Check if modal is closed
    expect(screen.queryByText(`Edit User: ${mockUsers[0].username}`)).not.toBeInTheDocument();
    
    // Check that API was not called
    expect(axios.put).not.toHaveBeenCalled();
  });

  test('handles user deletion with confirmation', async () => {
    // Mock successful API calls
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    axios.delete.mockResolvedValueOnce({});
    
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Delete')[1]).toBeInTheDocument();
    });
    
    // Click delete button for second user (non-admin)
    fireEvent.click(screen.getAllByText('Delete')[1]);
    
    await waitFor(() => {
      // Check if confirmation was shown
      expect(window.confirm).toHaveBeenCalledWith(`Are you sure you want to delete user ${mockUsers[1].username}?`);
      
      // Check if API was called with correct parameters
      expect(axios.delete).toHaveBeenCalledWith(
        `http://localhost:5000/api/v1/users/${mockUsers[1].username}`,
        {
          headers: {
            'Authorization': 'Bearer fake-admin-token'
          }
        }
      );
      
      // Check if users are fetched again
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
    
    // Restore original window.confirm
    window.confirm = originalConfirm;
  });

  test('handles user deletion cancellation', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => false);
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Delete')[1]).toBeInTheDocument();
    });
    
    // Click delete button for second user
    fireEvent.click(screen.getAllByText('Delete')[1]);
    
    // Check if confirmation was shown
    expect(window.confirm).toHaveBeenCalledWith(`Are you sure you want to delete user ${mockUsers[1].username}?`);
    
    // Check that API was not called
    expect(axios.delete).not.toHaveBeenCalled();
    
    // Restore original window.confirm
    window.confirm = originalConfirm;
  });

  test('disables delete button for admin users', async () => {
    // Mock successful API call
    axios.get.mockResolvedValueOnce({
      data: mockUsers
    });
    
    renderWithRouter(<AdminPanel />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Delete')[0]).toBeInTheDocument();
    });
    
    // Check if delete button for admin user is disabled
    const deleteButtons = screen.getAllByText('Delete');
    expect(deleteButtons[0].closest('button')).toBeDisabled();
    expect(deleteButtons[0].closest('button')).toHaveStyle('opacity: 0.5');
    
    // Check if delete buttons for non-admin users are enabled
    expect(deleteButtons[1].closest('button')).not.toBeDisabled();
    expect(deleteButtons[1].closest('button')).toHaveStyle('opacity: 1');
    expect(deleteButtons[2].closest('button')).not.toBeDisabled();
    expect(deleteButtons[2].closest('button')).toHaveStyle('opacity: 1');
  });
}); 
//npm test -- src/__tests__/components/adminPanel.test.js