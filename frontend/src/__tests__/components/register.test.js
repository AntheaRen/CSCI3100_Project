import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import Register from '../../component/register';

// Mock axios
jest.mock('axios');
// Mock useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate,
}));

describe('Register Component', () => {
  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();
  });

  test('renders register form correctly', () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    expect(screen.getByRole('heading', { name: 'Register' })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
    expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
  });

  test('handles input changes', () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/^password:/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    fireEvent.change(usernameInput, { target: { value: 'newuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    
    expect(usernameInput.value).toBe('newuser');
    expect(passwordInput.value).toBe('password123');
    expect(confirmPasswordInput.value).toBe('password123');
  });

  test('shows error when passwords do not match', async () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    // Fill in form with mismatched passwords
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'newuser' } });
    fireEvent.change(screen.getByLabelText(/^password:/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'password456' } });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /register/i }));
    
    // Check if error message is displayed
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    
    // Verify axios was not called
    expect(axios.post).not.toHaveBeenCalled();
  });

  test('handles successful registration', async () => {
    // Mock successful registration response
    axios.post.mockResolvedValueOnce({
      status: 201,
      data: {
        message: 'User registered successfully',
        username: 'newuser',
        credits: 10
      }
    });
    
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'newuser' } });
    fireEvent.change(screen.getByLabelText(/^password:/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'password123' } });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /register/i }));
    
    // Wait for axios call to resolve
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        'http://127.0.0.1:5000/api/v1/register',
        {
          username: 'newuser',
          password: 'password123'
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Check if navigation occurred to login page
      expect(mockedNavigate).toHaveBeenCalledWith('/login');
    });
  });

  test('handles registration error', async () => {
    // Mock failed registration
    axios.post.mockRejectedValueOnce({
      response: {
        data: {
          error: 'Username already exists'
        }
      }
    });
    
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'existinguser' } });
    fireEvent.change(screen.getByLabelText(/^password:/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'password123' } });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /register/i }));
    
    // Check if error message is displayed
    await waitFor(() => {
      expect(screen.getByText('Username already exists')).toBeInTheDocument();
    });
    
    // Verify navigation did not occur
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  test('login link navigates to login page', () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
    
    // Find the login link
    const loginLink = screen.getByText(/login/i).closest('a');
    expect(loginLink).toHaveAttribute('href', '/login');
  });
}); 
//npm test -- src/__tests__/components/register.test.js