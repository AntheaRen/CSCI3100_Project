from app import app, db
from modules.user import User
from modules.image import OutputImage

def check_db():
    with app.app_context():
        # Check users
        users = User.query.all()
        print("\nUsers in database:")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Credits: {user.credits}")
            
        # Check tables
        tables = db.engine.table_names()
        print("\nTables in database:", tables)
        
        # Check relationships
        print("\nDatabase structure:")
        for table in db.metadata.tables.values():
            print(f"\nTable: {table.name}")
            print("Columns:")
            for column in table.columns:
                print(f"  - {column.name}: {column.type}")
            if table.foreign_keys:
                print("Foreign Keys:")
                for fk in table.foreign_keys:
                    print(f"  - {fk.parent.name} -> {fk.target_fullname}")

if __name__ == '__main__':
    check_db() 