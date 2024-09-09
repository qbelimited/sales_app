from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Paypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True, unique=True)  # Ensure uniqueness if necessary
    location = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name')
    def validate_name(self, key, name):
        if not name:
            raise ValueError("Paypoint name cannot be empty")
        return name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_paypoints(page=1, per_page=10):
        """Retrieve paginated list of active paypoints."""
        try:
            return Paypoint.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active paypoints: {e}")
