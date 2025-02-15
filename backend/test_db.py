from app import app, db
from models.user import User

def test_db_operations():
    with app.app_context():
        # Create user
        def create_user(username, email, password):
            user = User(username=username, email=email)
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
        create_user("testuser1", "test1@example.com", "password123")
        get_user("testuser1")
        update_credits("testuser1", 50)
        delete_user("testuser1")

if __name__ == '__main__':
    test_db_operations() 