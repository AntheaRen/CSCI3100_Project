import os
import sys
import pytest
# Add the parent directory to sys.path so Python can find the app module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app, db
from modules.user import User


def test_db_operations():
    with app.app_context():
        db.create_all()
        # Create user
        def create_user(username, password):
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {username}")

        # Read user
        def get_user(username):
            user = User.query.filter_by(username=username).first()
            if user:
                print(f"Found user: {user.username}, Credits: {user.credits}")
            return user

        # Update user
        def update_credits(username, new_credits):
            user = get_user(username)
            if user:
                user.credits = new_credits
                db.session.commit()
                print(f"Updated credits for {username} to {new_credits}")

        # Delete user
        def delete_user(username):
            user = get_user(username)
            if user:
                db.session.delete(user)
                db.session.commit()
                print(f"Deleted user: {username}")

        # Test operations
        create_user("testuser1", "password123")
        user = get_user("testuser1")
        assert user.generated_images_count == 0, "generated_images_count should be initialized to 0"
        print(f"generated_images_count for {user.username}: {user.generated_images_count}")
        update_credits("testuser1", 50)
        delete_user("testuser1")


if __name__ == '__main__':
    test_db_operations()

#pytest tests/test_db.py -v