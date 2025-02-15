from app import app, db
from models.user import User

def view_users():
    with app.app_context():
        users = User.query.all()
        print("\nAll Users in Database:")
        print("-" * 50)
        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Credits: {user.credits}")
            print(f"Admin: {user.is_admin}")
            print("-" * 50)

if __name__ == '__main__':
    view_users() 