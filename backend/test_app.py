import os
import pytest
import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime

from app import app, db, jwt_blocklist
from modules.user import User
from modules.image import OutputImage
from modules.api import ArtifyAPI
from modules.webui import WebUI
from modules.upscaler import ESRGANUpscaler

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
            
            # Mock the API
            app.config['_mock_api'] = MockAPI()
            
            yield client
            
            # Clean up
            db.session.remove()
            db.drop_all()

def get_auth_token(client, username, password):
    """Helper function to get auth token"""
    response = client.post('/api/v1/login', 
                          json={'username': username, 'password': password})
    return json.loads(response.data)['access_token']

def test_register(client):
    """Test user registration"""
    # Test successful registration
    response = client.post('/api/v1/register', 
                          json={'username': 'newuser', 'password': 'newpass123'})
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'access_token' in data
    
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
    assert len(data['users']) >= 2
    
    # Test non-admin access
    response = client.get('/api/v1/users', 
                         headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 403
    
    # Test update user (admin only)
    response = client.put('/api/v1/users/testuser', 
                         json={'credits': 50},
                         headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    
    # Verify credits updated
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user.credits == 50

def test_text_to_image(client):
    """Test text-to-image endpoint"""
    # Get auth token
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Test t2i endpoint
    response = client.post('/api/v1/t2i', 
                          json={
                              'prompt': 'test prompt',
                              'negativePrompt': 'test negative',
                              'settings': {
                                  'width': 512,
                                  'height': 512,
                                  'batchSize': 1,
                                  'batchCount': 1,
                                  'cfgScale': 7.0,
                                  'samplingSteps': 20,
                                  'seed': 42
                              }
                          },
                          headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert 'image_ids' in data
    assert len(data['images']) == 1
    
    # Verify image was saved to database
    with app.app_context():
        image_id = data['image_ids'][0]
        image = OutputImage.query.get(image_id)
        assert image is not None
        assert image.prompt == 'test prompt'
        assert image.negative_prompt == 'test negative'

def test_upscale(client):
    """Test upscale endpoint"""
    # First create an image to upscale
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Create a test image
    test_img = Image.new('RGB', (64, 64), color='blue')
    buffered = BytesIO()
    test_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Test upscale endpoint
    response = client.post('/api/v1/upscale', 
                          json={
                              'image': img_str,
                              'ratio': 2.0
                          },
                          headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'image' in data
    
    # Decode and verify upscaled image
    upscaled_data = base64.b64decode(data['image'])
    upscaled_img = Image.open(BytesIO(upscaled_data))
    assert upscaled_img.size == (128, 128)  # Should be 2x the original

def test_user_images(client):
    """Test user image management endpoints"""
    # Get auth token
    token = get_auth_token(client, 'testuser', 'test123')
    
    # Create a test image in the database
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        output_image = OutputImage(
            user_id=user.id,
            filename='test_image.png',
            created_at=datetime.now(),
            prompt='test prompt',
            negative_prompt='test negative'
        )
        db.session.add(output_image)
        db.session.commit()
        image_id = output_image.id
    
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

if __name__ == '__main__':
    pytest.main(['-xvs', __file__])