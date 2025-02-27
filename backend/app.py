from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from models.user import db, User
from config import Config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Remove all CORS configurations and use the simplest possible one
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

db.init_app(app)
jwt = JWTManager(app)

# Create database tables
with app.app_context():
    db.create_all()

# Add this near your other app configurations
jwt_blocklist = set()

@app.route('/api/v1/register', methods=['POST'])
def register():
    try:
        # Check if JSON data exists
        if not request.is_json:
            return jsonify({'error': 'Missing JSON data'}), 400
            
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        #if User.query.filter_by(email=data['email']).first():
        #    return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            #email=data['email'],
            credits=data.get('credits', 10),  # Default to 10 if not specified
            is_admin=0
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'username': user.username,
            #'email': user.email,
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
        access_token = create_access_token(identity=user.username)
        return jsonify({
            'username': user.username,
            'credits': user.credits,
            'is_admin': user.is_admin,
            'access_token': access_token
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/v1/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]  # Get the unique identifier of the JWT token
    jwt_blocklist.add(jti)  # Add the token to blocklist
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/v1/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
        

@app.route('/api/v1/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'username': user.username,
            #'email': user.email,
            'credits': user.credits,
            'is_admin': user.is_admin
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/v1/users/<username>/credits', methods=['PUT'])
@jwt_required()
def update_credits(username):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    user = User.query.filter_by(username=username).first()
    if user:
        data = request.get_json()
        user.credits = data['credits']
        db.session.commit()
        return jsonify({'message': 'Credits updated successfully'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/v1/users/<username>', methods=['DELETE'])
@jwt_required()
def delete_user(username):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/v1/test', methods=['GET'])
def test():
    return("Hello World")

# Add this callback to check if a token is revoked
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in jwt_blocklist

if __name__ == '__main__':
    app.run(debug=True)
