from werkzeug.security import generate_password_hash, check_password_hash
from .database import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    credits = db.Column(db.Integer, default=10)
    is_admin = db.Column(db.Boolean, default=False)
    generated_images_count = db.Column(db.Integer, default=0)  # New field

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'username': self.username,
            'credits': self.credits,
            'is_admin': self.is_admin
        }
