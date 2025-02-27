from app import app, db
from models.user import User

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create sample users
        admin = User(
            username='admin',
            #email='admin@example.com',
            is_admin=True,
            credits=100
        )
        admin.set_password('admin123')
        
        user = User(
            username='testuser',
            #email='test@example.com',
            credits=10
        )
        user.set_password('test123')
        
        # Add users to database
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()
        
        print("Database initialized with sample users!")

if __name__ == '__main__':
    init_db() 