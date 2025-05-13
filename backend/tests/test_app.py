import os
import sys
import pytest
# Add the parent directory to sys.path so Python can find the app module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import unittest.mock

from app import app, db, jwt_blocklist
from modules.user import User
from modules.image import OutputImage
from modules.api import ArtifyAPI

# Mock classes to avoid actual API calls during testing
class MockWebUI:
    def txt2img(self, prompt, **kwargs):
        # Return a simple test image
        img = Image.new('RGB', (64, 64), color='red')
        return [img]
        
    def upscale(self, image, ratio=2.0):
        # Return a simple upscaled test image
        width, height = image.size
        return image.resize((int(width * ratio), int(height * ratio)))

class MockAPI:
    def __init__(self):
        self.image_generator = MockWebUI()
        self.upscaler = MockWebUI()
        
    def txt2img(self, prompt, **kwargs):
        return self.image_generator.txt2img(prompt, **kwargs)
        
    def upscale(self, image, ratio=2.0):
        return self.upscaler.upscale(image, ratio)

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    
    # Create test client
    with app.test_client() as client:
        # Create application context
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create test users
            admin = User(username='admin', credits=100, is_admin=True)
            admin.set_password('admin123')
            
            user = User(username='testuser', credits=10)
            user.set_password('test123')
            
            db.session.add_all([admin, user])
            db.session.commit()
            
            # Create necessary directories
            os.makedirs('outputs/t2i', exist_ok=True)
            os.makedirs(f'outputs/t2i/user_1', exist_ok=True)
            os.makedirs(f'outputs/t2i/user_2', exist_ok=True)
            
            # Mock the API
            # We'll patch the init_api function in tests that need it
            
            yield client
            
            # Clean up
            db.session.remove()
            db.drop_all()

def get_auth_token(client, username, password):
    """Helper function to get auth token"""
    response = client.post('/api/v1/login', 
                          json={'username': username, 'password': password})
    return json.loads(response.data)['access_token']

# Patch the register endpoint test to match your implementation
def test_register(client):
    """Test user registration"""
    # Test successful registration
    response = client.post('/api/v1/register', 
                          json={'username': 'newuser', 'password': 'newpass123'})
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'User created successfully'
    
    # Test duplicate username
    response = client.post('/api/v1/register', 
                          json={'username': 'newuser', 'password': 'anotherpass'})
    assert response.status_code == 400
    
    # Test missing fields
    response = client.post('/api/v1/register', json={'username': 'incomplete'})
    assert response.status_code == 400

def test_login(client):
    """Test user login"""
    # Test successful login
    response = client.post('/api/v1/login', 
                          json={'username': 'testuser', 'password': 'test123'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    
    # Test invalid credentials
    response = client.post('/api/v1/login', 
                          json={'username': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 401

def test_logout(client):
    """Test user logout"""
    # Get auth token
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Test logout
    response = client.post('/api/v1/logout', 
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    
    # Verify token is invalidated
    response = client.get('/api/v1/verify-token', 
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401

def test_verify_token(client):
    """Test token verification"""
    # Get auth token
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Test valid token
    response = client.get('/api/v1/verify-token', 
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is True

def test_user_management(client):
    """Test user management endpoints"""
    # Get admin token
    admin_token = get_auth_token(client, 'admin', 'admin123')
    user_token = get_auth_token(client, 'testuser', 'test123')
    
    # Test get all users (admin only)
    response = client.get('/api/v1/users', 
                         headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    # Your endpoint returns a list directly, not a dict with 'users' key
    assert len(data) >= 2  # At least admin and testuser
    
    # Test non-admin access
    response = client.get('/api/v1/users', 
                         headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 403
    
    # Test update user (admin only)
    # Use the correct endpoint for updating users based on your app.py
    response = client.put('/api/v1/users/testuser', 
                         json={'credits': 50},
                         headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    
    # Verify credits updated - use the get_user endpoint
    response = client.get('/api/v1/users/testuser',
                         headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['credits'] == 50



def test_user_images(client):
    """Test user image management endpoints"""
    # Get auth token
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Create a test image in the database
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        output_image = OutputImage(
            user_id=user.id,
            created_at=datetime.now(),
            prompt='test prompt',
            negative_prompt='test negative'
        )
        db.session.add(output_image)
        db.session.commit()
        image_id = output_image.id
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_image.path), exist_ok=True)
        
        # Create a dummy image file for testing
        test_img = Image.new('RGB', (64, 64), color='red')
        test_img.save(output_image.path)
    
    # Test get user images
    response = client.get('/api/v1/images', 
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert len(data['images']) >= 1
    
    # Test delete image
    response = client.delete(f'/api/v1/images/{image_id}', 
                            headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    
    # Verify image was deleted
    with app.app_context():
        image = OutputImage.query.get(image_id)
        assert image is None




def test_generate_image_increments_count(client):
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Create a mock API
    mock_api = MockAPI()
    
    # Patch both the global api variable and init_api function
    with unittest.mock.patch('app.api', mock_api), \
         unittest.mock.patch('app.init_api', return_value=mock_api):
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            before_count = user.generated_images_count

        data = {
            "prompt": "A red square",
            "negativePrompt": "",
            "settings": {
                "batchSize": 1,
                "batchCount": 1,
                "width": 64,
                "height": 64,
                "cfgScale": 7.0,
                "samplingSteps": 20,
                "sampler": "Euler Ancestral CFG++"
            }
        }

        response = client.post(
            '/api/v1/t2i',
            json=data,
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            after_count = user.generated_images_count

        assert after_count == before_count + 1

if __name__ == '__main__':
    pytest.main(['-xvs', __file__])

#pytest -v tests/test_app.py