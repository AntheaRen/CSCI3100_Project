import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import NavBar from '../../component/navBar';

// Mock axios
jest.mock('axios');

// Mock useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate,
}));

describe('NavBar Component', () => {
  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();
    
    // Reset localStorage before each test
    localStorage.clear();
  });

  test('renders navbar with all links for regular user', () => {
    // Set up localStorage with a regular user
    localStorage.setItem('currentUser', JSON.stringify({
      username: 'testuser',
      isAdmin: false,
      token: 'fake-token-123'
    }));
    
    render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Check logo and navigation links
    expect(screen.getByText('AI Image Generator')).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Generate')).toBeInTheDocument();
    expect(screen.getByText('Gallery')).toBeInTheDocument();
    expect(screen.getByText('Upscale')).toBeInTheDocument();
    
    // Check user info
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
    
    // Admin panel should not be visible for regular users
    expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
    expect(screen.queryByText('Admin')).not.toBeInTheDocument();
  });

  test('renders navbar with admin panel for admin user', () => {
    // Set up localStorage with an admin user
    localStorage.setItem('currentUser', JSON.stringify({
      username: 'adminuser',
      isAdmin: true,
      token: 'fake-admin-token'
    }));
    
    render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Check for admin-specific elements
    expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  test('handles logout successfully', async () => {
    // Set up localStorage with a user
    localStorage.setItem('currentUser', JSON.stringify({
      username: 'testuser',
      isAdmin: false,
      token: 'fake-token-123'
    }));
    
    // Mock successful logout
    axios.post.mockResolvedValueOnce({});
    
    render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Click logout button
    fireEvent.click(screen.getByText('Logout'));
    
    // Wait for axios call to resolve
    await waitFor(() => {
      // Check if API was called with correct parameters
      expect(axios.post).toHaveBeenCalledWith(
        'http://127.0.0.1:5000/api/v1/logout', 
        {}, 
        {
          headers: {
            'Authorization': 'Bearer fake-token-123',
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Check if localStorage was cleared
      expect(localStorage.getItem('currentUser')).toBeNull();
      
      // Check if navigation occurred
      expect(mockedNavigate).toHaveBeenCalledWith('/login');
    });
  });

  test('handles logout error gracefully', async () => {
    // Set up localStorage with a user
    localStorage.setItem('currentUser', JSON.stringify({
      username: 'testuser',
      isAdmin: false,
      token: 'fake-token-123'
    }));
    
    // Mock failed logout
    axios.post.mockRejectedValueOnce(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Click logout button
    fireEvent.click(screen.getByText('Logout'));
    
    // Wait for axios call to resolve
    await waitFor(() => {
      // Even if API call fails, localStorage should be cleared
      expect(localStorage.getItem('currentUser')).toBeNull();
      
      // Navigation should still occur
      expect(mockedNavigate).toHaveBeenCalledWith('/login');
    });
  });

  test('navigation links have correct hrefs', () => {
    // Set up localStorage with a user
    localStorage.setItem('currentUser', JSON.stringify({
      username: 'testuser',
      isAdmin: false,
      token: 'fake-token-123'
    }));
    
    render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Check href attributes of links
    expect(screen.getByText('Home').closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByText('Generate').closest('a')).toHaveAttribute('href', '/generator');
    expect(screen.getByText('Gallery').closest('a')).toHaveAttribute('href', '/gallery');
    expect(screen.getByText('Upscale').closest('a')).toHaveAttribute('href', '/upscale');
  });

  test('renders nothing when no user is logged in', () => {
    // No user in localStorage
    
    const { container } = render(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // The navbar should not render anything when no user is logged in
    expect(container.firstChild).toBeNull();
  });
}); 
//npm test -- src/__tests__/components/navBar.test.js