import os
import sys
import pytest
# Add the parent directory to sys.path so Python can find the app module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app, db
from modules.user import User
from modules.image import OutputImage
from PIL import Image
import os

def test_image_storage():
    with app.app_context():
        # Get test user
        user = User.query.filter_by(username='testuser').first()
        
        # Create test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Create image record
        output_image = OutputImage(
            user_id=user.id,
            filename='test_image.png',
            prompt='Test prompt',
            negative_prompt='Test negative prompt'
        )
        
        # Save to database
        db.session.add(output_image)
        db.session.commit()
        
        # Create directory and save image
        os.makedirs(os.path.dirname(output_image.path), exist_ok=True)
        test_image.save(output_image.path)
        
        print(f"Created image record: ID={output_image.id}")
        print(f"Saved image to: {output_image.path}")
        
        # Verify relationship
        print(f"\nUser {user.username} has {len(user.images)} images")
        for img in user.images:
            print(f"- Image {img.id}: {img.path}")

if __name__ == '__main__':
    test_image_storage() 

#pytest tests/test_image_db.py -v