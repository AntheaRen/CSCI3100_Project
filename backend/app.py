from flask import Flask, request, jsonify
from flask_cors import CORS
from models.user import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/api/v1/register', methods=['POST'])
def register():
    try:
        # Check if JSON data exists
        if not request.is_json:
            return jsonify({'error': 'Missing JSON data'}), 400
            
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            credits=data.get('credits', 10)  # Default to 10 if not specified
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'username': user.username,
            'email': user.email,
            'credits': user.credits
        }), 201
        
    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        db.session.rollback()
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/api/v1/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        return jsonify({
            'username': user.username,
            'credits': user.credits,
            'is_admin': user.is_admin
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/v1/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'credits': user.credits,
            'is_admin': user.is_admin
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/v1/users/<username>/credits', methods=['PUT'])
def update_credits(username):
    user = User.query.filter_by(username=username).first()
    if user:
        data = request.get_json()
        user.credits = data['credits']
        db.session.commit()
        return jsonify({'message': 'Credits updated successfully'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/v1/users/<username>', methods=['DELETE'])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
