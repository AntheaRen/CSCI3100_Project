from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from modules.user import db, User
from modules.image import OutputImage
from config import Config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta
import os
import base64
import io
import traceback
from PIL import Image
import torch
import random
from typing import List


app = Flask(__name__, static_folder='static', static_url_path="")


# @app.route("/")
# def serve_frontend():
#     return send_from_directory("static", "index.html")


# @app.route("/<path:filename>")
# def serve_static(filename):
#     return send_from_directory("static", filename)


# @app.route("/<path:subpath>")
# def handle_frontend_routes(subpath):
#     return send_from_directory("static", "index.html")


# @app.route("/", defaults={"subpath": ""})
# @app.route("/<path:subpath>")
# def serve_any_path(subpath):
#     return send_from_directory("static", "index.html")


app.config.from_object(Config)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Remove all CORS configurations and use the simplest possible one
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

db.init_app(app)
jwt = JWTManager(app)

# Create database tables
with app.app_context():
    db.create_all()

# Add this near your other app configurations
jwt_blocklist = set()


def get_current_user():
    print(f"jwt_identity: {get_jwt_identity()}")
    return User.query.filter_by(username=get_jwt_identity()).first()


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

        # if User.query.filter_by(email=data['email']).first():
        #    return jsonify({'error': 'Email already exists'}), 400

        # Create new user
        user = User(
            username=data['username'],
            # email=data['email'],
            credits=data.get('credits', 10),  # Default to 10 if not specified
            is_admin=0
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'username': user.username,
            # 'email': user.email,
            'credits': user.credits
        }), 201

    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        db.session.rollback()
        return jsonify({'error': 'Server error occurred'}), 500


@app.route('/api/v1/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.username)
        print(f"[Debug] User {user.username} logged in. Access token: {access_token}")
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
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403


@app.route('/api/v1/users/<username>', methods=['GET'])
def get_user(username):
    user = get_current_user()
    if user:
        return jsonify({
            'username': user.username,
            # 'email': user.email,
            'credits': user.credits,
            'is_admin': user.is_admin
        })
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/v1/users/<username>/credits', methods=['PUT'])
@jwt_required()
def update_credits(username):
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403

    target_user = User.query.filter_by(username=username).first()
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    target_user.credits = data['credits']
    db.session.commit()


@app.route('/api/v1/users/<username>', methods=['DELETE'])
@jwt_required()
def delete_user(username):
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403

    user = get_current_user()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/v1/test', methods=['GET'])
def test():
    return ("Hello World")

# Add this callback to check if a token is revoked


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in jwt_blocklist


# @celery.task
# def t2i_inference(
#     pipeline,
#     prompt: str,
#     negative_prompt: str,
#     width: int,
#     height: int,
#     batch_size: int,
#     batch_count: int,
#     guidance_scale: float,
#     num_inference_steps: int,
#     seed: int,
# ):
#     return pipeline.generate(
#         prompt=prompt,
#         negative_prompt=negative_prompt,
#         width=width,
#         height=height,
#         batch_size=batch_size,
#         batch_count=batch_count,
#         guidance_scale=guidance_scale,
#         num_inference_steps=num_inference_steps,
#         seed=seed
#     )


@app.route('/api/v1/t2i', methods=['POST'])
@jwt_required()
def t2i():
    """
    Text-to-Image API
    Cost: 2 credit per image
    """
    try:
        # Test code
        # image_path = r"C:\Users\15070\Desktop\History Courses\yr4 Term2\CSCI3100\CSCI3100_Project\backend\outputs\t2i\0.png"
        # with open(image_path, 'rb') as f:
        #     img_str = base64.b64encode(f.read()).decode()

        # return jsonify({'images': [img_str]})

        from modules import sd
        data = request.get_json()
        settings = data.get('settings', {})
        batch_size = int(settings.get('batchSize', 1))
        batch_count = int(settings.get('batchCount', 1))

        user = get_current_user()

        required_credits = batch_size * batch_count * 2
        left_credits = user.credits

        if left_credits < required_credits:
            return jsonify({'error': 'Insufficient credits'}), 402
        else:
            user.credits = left_credits - required_credits
            db.session.commit()

        if sd.api is None:
            # sd.api = sd.Pipeline(
            #     pretrained_model_name_or_path="/root/autodl-tmp/stable-diffusion-webui/models/Stable-diffusion/noob_eps_v1-1.safetensors",
            #     enable_xformers_memory_efficient_attention=False,
            #     device="cuda",
            #     torch_dtype=torch.float16
            # )
            sd.api = sd.WebUIAPI(
                host='connect.yza1.seetacloud.com',
                port=12007,
                username='root',
                password='vs6lNM5wi0aq',
            )

        # Generate images
        if settings.get('seed'):
            seed = int(settings['seed'])
        else:
            seed = random.randint(0, 2**32 - 1)
        images: List[Image.Image] = sd.api.generate(
            prompt=data.get('prompt'),
            negative_prompt=data.get('negativePrompt'),
            width=int(settings.get('width', 512)),
            height=int(settings.get('height', 512)),
            batch_size=batch_size,
            batch_count=batch_count,
            guidance_scale=float(settings.get('cfgScale', 7.0)),
            num_inference_steps=int(settings.get('samplingSteps', 20)),
            seed=seed
        )

        # Save images to output directory
        image_paths = []
        for i, image in enumerate(images):
            output_image = OutputImage(user_id=user.id)
            # db.session.add(output_image)
            # db.session.commit()
            os.makedirs(os.path.dirname(output_image.path), exist_ok=True)
            image.save(output_image.path)
            print(f"Saved image {output_image.id} to {output_image.path}")
            image_paths.append(output_image.path)

        # Convert images to base64
        image_data = []
        for image_path in image_paths:
            with open(image_path, 'rb') as f:
                image_data.append(base64.b64encode(f.read()).decode())

        return jsonify({'images': image_data})

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Server error occurred'}), 500


@app.route('/api/v1/upscale', methods=['POST'])
@jwt_required()
def upscale():
    """
    Upscale API
    Cost: 1 credit per image
    """
    try:
        required_credits = 1
        left_credits = get_current_user().credits

        if left_credits < required_credits:
            return jsonify({'error': 'Insufficient credits'}), 402
        else:
            user = get_current_user()
            user.credits = left_credits - required_credits
            db.session.commit()

        from modules import upscaler
        if upscaler.upscaler is None:
            upscaler.upscaler = upscaler.Upscaler.from_single_file(
                pretrained_model_name_or_path=upscaler.DEFAULT_PRETRAINED_MODEL_NAME_OR_PATH,
                device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
                verbose=True
            )

        data = request.get_json()
        image = Image.open(io.BytesIO(base64.b64decode(data['image'])))
        image = upscaler.upscaler(image)
        buffered = io.BytesIO()
        image[0].save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return jsonify({'image': img_str})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
