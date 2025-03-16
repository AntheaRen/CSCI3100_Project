import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class OutputImage(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def path(self):
        return os.path.join("database", "images", str(self.user_id), f"{self.id}.png")
