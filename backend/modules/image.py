from datetime import datetime
import os
from .database import db


class OutputImage(db.Model):
    __tablename__ = 'output_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    prompt = db.Column(db.Text)
    negative_prompt = db.Column(db.Text)

    # Define the relationship here only
    user = db.relationship('User', backref=db.backref('images', lazy=True))

    @property
    def path(self):
        """Get the full path to the image file"""
        return os.path.join('outputs', 't2i', f'user_{self.user_id}', f'image_{self.id}.png')
