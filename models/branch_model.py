from app import db
from datetime import datetime

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    ghpost_gps = db.Column(db.String(100), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    users = db.relationship('User', backref='branch', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'region': self.region,
            'ghpost_gps': self.ghpost_gps,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'users': [user.id for user in self.users]  # Serialize user IDs associated with this branch
        }
